# encoding: utf-8
import decimal
import logging
from datetime import timedelta

import braintree
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User as AuthUser
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_choices_enum import ChoicesEnum

logger = logging.getLogger(__name__)

GSUITE_PRODUCT_CATEGORY_NAME = 'GSUITE'


class Enum(str, ChoicesEnum):
    pass


class LowerCaseCharField(models.CharField):
    """
    Defines a charfield which automatically converts all inputs to
    lowercase and saves.
    """

    def pre_save(self, model_instance, add):
        """
        Converts the string to lowercase before saving.
        """
        current_value = getattr(model_instance, self.attname)
        if current_value:
            setattr(model_instance, self.attname, current_value.lower())
        return getattr(model_instance, self.attname)


# Create your models here.
class CustomerType(Enum):
    CUSTOMER = ('CUSTOMER', _('Customer'))
    ECONSULTING_CUSTOMER = ('ECONSULTING_CUSTOMER', _('Econsulting Customer'))
    ECONSULTING_PARTNER = ('ECONSULTING_PARTNER', _('Econsulting Partner'))
    ECONSULTING_PROSPECT = ('ECONSULTING_PROSPECT', _('Econsulting Prospect'))
    ECONSULTING_RESELLER = ('ECONSULTING_RESELLER', _('Econsulting Reseller'))
    EX_RESELLER = ('EX_RESELLER', _('Ex - Reseller'))
    GAE_RESELLER = ('GAE_RESELLER', _('GAE Reseller'))
    GOOGLE_APPS_RESELLER = ('GOOGLE_APPS_RESELLER', _('Google Apps Reseller'))
    PROSPECT = ('PROSPECT', _('Prospect'))
    RESOLD_PROSPECT = ('RESOLD_PROSPECT', _('Resold Prospect'))
    RESOLD_CUSTOMER = ('RESOLD_CUSTOMER', _('Resold Customer'))


class CustomerNameMixIn(object):
    customer = None

    @property
    def customer_name(self):
        return self.customer.name


class Auditable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(Auditable):
    name = LowerCaseCharField(max_length=255, unique=True)
    org_name = models.CharField(blank=True, null=True, max_length=1023)
    type = models.CharField(choices=CustomerType.choices(), default=CustomerType.PROSPECT.value, max_length=31)
    reseller = models.ForeignKey('Customer', related_name='customers', blank=True, null=True)
    reseller_name = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=31, default='USD')
    offline = models.BooleanField(default=False)
    tax = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    balance = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    install_status = models.CharField(blank=True, null=True, max_length=255)
    source = models.CharField(blank=True, null=True, max_length=255)
    registered = models.BooleanField(default=False)
    last_payment_date_raw = models.DateTimeField(null=True, blank=True)
    last_payment_outcome_raw = models.CharField(max_length=255, null=True, blank=True)
    last_payment_id_raw = models.CharField(max_length=255, null=True, blank=True)
    last_payment_type = models.CharField(max_length=255, null=True, blank=True)
    communication_user = models.ForeignKey('User', related_name="+", blank=True, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        db_table = 'sm_customer'

    @property
    def verbose_name(self):
        return self.org_name if self.org_name else self.name

    def get_communication_user(self):
        if not self.communication_user:
            self.communication_user = User.objects.filter(customer=self).order_by('-modified_at').first()
        return self.communication_user

    def set_communication_user(self, user, save=False):
        self.communication_user = user
        if save:
            self.save(update_fields=['communication_user'])

    @property
    def total_revenue(self):
        return sum([order.total for order in Order.objects.filter(
            customer=self, status=OrderStatus.PAID)])

    @property
    def payment_position(self):
        return Order.objects.filter(
            customer=self, status=OrderStatus.PAID).count()

    @property
    def first_payment_date(self):
        order = get_first_payment_order(self)
        if order:
            return order.date

    @property
    def first_payment_id(self):
        order = get_first_payment_order(self)
        if order:
            return get_payment_id(order)

    @property
    def last_payment_amount(self):
        order = get_last_payment_order(self)
        if order:
            return order.total
        return

    def _set_last_payment_outcome(self, outcome):
        self.last_payment_outcome_raw = outcome

    def _get_last_payment_outcome(self):
        if self.last_payment_outcome_raw:
            return self.last_payment_outcome_raw

        last_success = BraintreeTransaction.objects.filter(
            order__customer=self, status="Completed").order_by("-completed_date").first()
        last_error = BraintreeTransaction.objects.filter(
            order__customer=self, status="Error").order_by("-completed_date").first()

        if last_error and (
                not last_success or last_error.completed_date > last_success.completed_date):
            return last_error.error
        elif last_success:
            return "Success"
        return

    def _get_last_payment_date(self):
        if self.last_payment_date_raw:
            return self.last_payment_date_raw
        order = get_last_payment_order(self)
        if order:
            return order.date

    def _set_last_payment_date(self, date):
        self.last_payment_date_raw = date

    def _set_last_payment_id(self, payment_id):
        self.last_payment_id_raw = payment_id

    def _get_last_payment_id(self):
        if self.last_payment_id_raw:
            return self.last_payment_id_raw
        else:
            order = get_last_payment_order(self)
            if order:
                return get_payment_id(order)
            return

    last_payment_date = property(_get_last_payment_date, _set_last_payment_date)
    last_payment_outcome = property(_get_last_payment_outcome,
                                    _set_last_payment_outcome)
    last_payment_id = property(_get_last_payment_id, _set_last_payment_id)

    def set_last_payment_status(self, outcome, payment_id, date=None):
        if not date:
            date = timezone.now()

        self.last_payment_date = date
        self.last_payment_id = payment_id
        self.last_payment_outcome = outcome


class Profile(Auditable, CustomerNameMixIn):
    customer = models.ForeignKey('Customer', related_name='profile_set')
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.customer.name

    class Meta:
        db_table = 'sm_profile'


class Vendor(models.Model):
    """
    A company that owns some the products whose subscriptions we are managing.
    :model:
        name: the name of this vendor
        url: the website of this vendor
    """
    name = models.CharField(max_length=255, blank=False)
    url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sm_vendor'


class VendorProfile(Auditable, CustomerNameMixIn):
    """
        VendorProfile is the profile of the customer held by the vendor
    """
    customer = models.ForeignKey('Customer', related_name="vendor_profile_set")
    name = models.CharField(max_length=255, unique=True, verbose_name="Domain Name")
    primary = models.BooleanField(default=False, verbose_name="Is Primary")
    org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Organization Name')
    lang = models.CharField(max_length=31, blank=True, null=True, verbose_name='Language Code')
    country = models.CharField(max_length=255, blank=True, null=True, verbose_name='Country Code')
    secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Secondary Email')
    users = models.IntegerField(blank=True, null=True, default=0, verbose_name='Users Number')
    apps_creation = models.DateTimeField(blank=True, null=True, verbose_name='Apps Creation')
    apps_expiry = models.DateTimeField(blank=True, null=True, verbose_name='Apps Expiry')
    apps_version = models.CharField(max_length=31, blank=True, null=True)
    max_licenses = models.IntegerField(blank=True, null=True, default=0, verbose_name='Max licenses')
    reseller = models.CharField(max_length=1023, blank=True, null=True)

    def __str__(self):
        return self.customer.name

    class Meta:
        db_table = 'sm_vendor_profile'

    @property
    def currency(self):
        from incf.countryutils import transformations
        if self.country:
            try:
                ctn = transformations.cca_to_ctn(self.country)
                if ctn == 'Europe':
                    return "EUR"
            except KeyError:
                pass
        return 'USD'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """Will also make a draft GSUITE subscription,
        and afterwards save the VendorProfile

        :param force_insert:
        :param force_update:
        :param using:
        :param update_fields:
        :return:
        """
        code = None
        if self.apps_version == 'standard':
            code = 'GSUITE_STANDARD_NO_PLAN'
        elif self.apps_version == 'premier':
            code = 'GSUITE_PREMIER_NO_PLAN'
        elif self.apps_version == 'government':
            code = 'GSUITE_GOVERNMENT_NO_PLAN'
        elif self.apps_version == 'education':
            code = 'GSUITE_EDU_NO_PLAN'
        elif self.apps_version == 'appsless':
            code = 'GSUITE_APSLESS_NO_PLAN'
        elif self.apps_version == 'basic':
            code = 'GSUITE_BASIC_NO_PLAN'
        elif self.apps_version == 'free':
            code = 'GSUITE_FREE_NO_PLAN'

        if code:
            product = Product.objects.filter(code=code)
            if product.exists():
                product = product.first()

                subscription = Subscription.objects.filter(
                    customer=self.customer,
                    product__category__code=GSUITE_PRODUCT_CATEGORY_NAME,
                    status=SubscriptionStatus.DRAFT.value
                )
                kwargs = dict(
                    vendor_licenses=self.users,
                    vendor_users=self.users,
                    product=product,
                    max_cap=self.max_licenses)
                if subscription.exists():
                    subscription.update(**kwargs)
                else:
                    # we should also NOT create a new subscription
                    # if a non-draft exists for that Product
                    subscription = Subscription.objects.filter(
                        customer=self.customer,
                        product__category__code=GSUITE_PRODUCT_CATEGORY_NAME,
                    )
                    if not subscription.exists():
                        catalog = Catalog.objects.filter(product=product,
                                                         default=True)
                        if catalog:
                            catalog = catalog.first()
                            subscription.create(
                                name="%s for %s" % (code, self.name),
                                customer=self.customer,
                                status=SubscriptionStatus.DRAFT.value,
                                vendor_status="",
                                domain=self.customer.name,
                                saw_price=False,
                                billable_licenses=self.users or 1,
                                catalog=catalog,
                                **kwargs
                            )
                        else:
                            logger.warn("TODO: Assign a Default catalog to this product {}".format(code))
            else:
                logger.error(
                    'Cannot create subscription from vendorProfile for {}.'
                    'Reason: no product for {}'
                        .format(self.customer, self.apps_version))

        super(VendorProfile, self).save(force_insert, force_update, using, update_fields)


class UserRole(Enum):
    BUYER = ('BUYER', _('Buyer'))
    ADMIN = ('ADMIN', _('Admin'))
    USER = ('USER', _('User'))


class BraintreePaymentMethod(Auditable):
    customer_id = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)
    succeed = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    type = models.CharField(max_length=31, choices=[("credit_card", "Credit Card"), ("paypal", "Paypal")], blank=True,
                            null=True)
    last_4_digits = models.CharField(max_length=15, blank=True, null=True)
    card_type = models.CharField(max_length=31, blank=True, null=True)
    expiration_date = models.CharField(max_length=255, blank=True, null=True)
    email_address = models.CharField(max_length=255, blank=True, null=True)
    detail = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sm_bt_payment_method'

    def __str__(self):
        return "{}:{}".format(self.customer_id, self.token)

    @property
    def customer(self):
        user = User.objects.get(auth_user__username=self.customer_id[3:])
        return user.customer


class User(Auditable, CustomerNameMixIn):
    customer = models.ForeignKey('Customer', related_name="users")
    name = models.CharField(max_length=255, blank=True, null=True)
    auth_user = models.OneToOneField(AuthUser, related_name='sm', null=True)
    email = LowerCaseCharField(max_length=255)
    contact_email = LowerCaseCharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    function = models.CharField(max_length=25, blank=True, null=True)
    role = models.CharField(choices=UserRole.choices(), default=UserRole.BUYER.value, max_length=31)
    mock = models.BooleanField(default=False)
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return self.email

    @property
    def first_name(self):
        name = self.name.split()
        return name[0] if len(name) > 1 else self.name

    @property
    def debug_login_url(self):
        if self.mock:
            from sm.core.user_token import user_token_factory
            from sm.core.auth import AUTH_TOKEN_KEY
            from django.core.urlresolvers import reverse
            key = user_token_factory.create(self.email, self.customer.name).key
            return reverse("frontend:login") + "?%s=%s" % (AUTH_TOKEN_KEY, key)
        raise Exception("%s is not a mock one!" % self.email)

    class Meta:
        db_table = 'sm_user'
        unique_together = (('customer', 'email'),)


class ProductVersionEnum(Enum):
    FREE = ('FREE', _('Free version'))
    BASIC = ('BASIC', _('Basic version'))
    PRO = ('PRO', _('Professional version'))
    ENTERPRISE = ('ENTERPRISE', _('Enterprise version'))
    BUSINESS = ('BUSINESS', _('Business version'))
    EVALUATION = ('EVALUATION', _('Evaluation version'))
    EDUCATION = ('EDUCATION', _('Education version'))

    def __lt__(self, y):
        if self == ProductVersionEnum.FREE and y in (ProductVersionEnum.BASIC,
                                                     ProductVersionEnum.PRO,
                                                     ProductVersionEnum.ENTERPRISE):
            return True
        elif self == ProductVersionEnum.BASIC and y in (ProductVersionEnum.PRO,
                                                        ProductVersionEnum.ENTERPRISE):
            return True
        elif self == ProductVersionEnum.PRO and y == ProductVersionEnum.ENTERPRISE:
            return True

        return False

    def __gt__(self, y):
        if not self == y and not self < y:
            return True
        return False


class ProductType(Enum):
    SUBSCRIPTION = ('SUBSCRIPTION', _('Subscription'))
    ONE_SHOT = ('ONE_SHOT', _('One-shot'))


class SubscriptionPlan(Enum):
    FLEXIBLE = ('FLEXIBLE', 'Flexible')
    FLEX_PREPAID = ('FLEX_PREPAID', 'Flex prepaid')
    ANNUAL_YEARLY = ('ANNUAL_YEARLY', 'Annual yearly')
    ANNUAL_MONTHLY = ('ANNUAL_MONTHLY', 'Annual monthly')
    UNKNOWN_PLAN = ('UNKNOWN_PLAN', 'Unknown plan')


class BillingCycleEnum(Enum):
    '''
    Describe when we should charge customer.
    END_OF_MONTH: we charge customer every 1st of every month.
    DATE_TO_DATE: we charge customer every X day of every month.
    '''
    END_OF_MONTH = ('END_OF_MONTH', _('End of month'))
    DATE_TO_DATE = ('DATE_TO_DATE', _('Date to date'))


class FrequencyEnum(Enum):
    MONTH = ('MONTH', 'Month')
    YEAR = ('YEAR', 'Year')

    @property
    def timedelta(self):
        if self.name == 'MONTH':
            return timedelta(days=30)
        elif self.name == 'YEAR':
            return timedelta(days=365)


class ProductPlan(models.Model):
    name = models.CharField(max_length=100)
    codename = models.CharField(
        max_length=31,
        choices=SubscriptionPlan.choices(),
        unique=True
    )
    toggle_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=150)
    description = models.CharField(max_length=200)
    billing_frequency = models.CharField(
        max_length=31,
        choices=FrequencyEnum.choices()
    )
    alternate_frequency = models.CharField(
        max_length=31,
        choices=FrequencyEnum.choices(),
        blank=True
    )
    commitment = models.CharField(
        max_length=31,
        choices=FrequencyEnum.choices()
    )
    billing_cycle = models.CharField(
        max_length=12,
        choices=BillingCycleEnum.choices()
    )

    class Meta:
        db_table = 'sm_plan'

    def __str__(self):
        return self.name


class ProductVersion(models.Model):
    codename = models.CharField(max_length=100,
                                unique=True,
                                choices=ProductVersionEnum.choices())
    name = models.CharField(max_length=100)
    extended_name = models.CharField(max_length=150)
    color_code = models.CharField(max_length=50)
    motto = models.CharField(max_length=200)
    product_category = models.ForeignKey('ProductCategory',
                                         related_name='product_versions')
    features = models.ManyToManyField('ProductFeature',
                                      through='FeatureVersion')
    sku = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'sm_version'

    def __str__(self):
        return self.name


class ProductFeature(models.Model):
    '''
    name: feature display name.
    product_category: product category to limit features during editing in admin
        panel.
    versions: all product versions that related with this feature.
    product_categories: all product categories that related with this product
        feature.
    '''
    name = models.CharField(max_length=100)
    product_category = models.ForeignKey('ProductCategory',
                                         related_name='product_features')
    versions = models.ManyToManyField('ProductVersion',
                                      through='FeatureVersion')
    product_categories = models.ManyToManyField('ProductCategory',
                                                through='FeatureProductCategory')

    class Meta:
        db_table = 'sm_feature'

    def __str__(self):
        return self.name


class FeatureVersion(models.Model):
    version = models.ForeignKey('ProductVersion',
                                related_name='feature_options')
    feature = models.ForeignKey('ProductFeature',
                                related_name='version_options')
    detail = models.CharField(max_length=100, blank=True)
    bold = models.BooleanField(default=False)
    position = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'sm_feature_version'
        unique_together = (('version', 'feature'),)

    def __str__(self):
        return '{} - {}'.format(self.feature.name, self.version.name)


class FeatureProductCategory(models.Model):
    product_category = models.ForeignKey('ProductCategory',
                                         related_name='feature_options')
    feature = models.ForeignKey('ProductFeature',
                                related_name='product_category_options')
    detail = models.CharField(max_length=100, blank=True)
    bold = models.BooleanField()
    position = models.IntegerField()

    class Meta:
        db_table = 'sm_feature_product_category'
        unique_together = (('product_category', 'feature'),)

    def __str__(self):
        return '{} - {}'.format(self.feature.name, self.product_category.name)


class ProductCategory(models.Model):
    '''
    name:
    code:
    vendor:
    logo_big:
    logo_small:
    parent_category:
    features:
    default_product: this product used in some business logic cases when we
        can't get product for example from user subscription. This field marked
        as null=True this to break recursion denedence of product and product
        category.
    '''
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, null=True, blank=True)
    logo_big = models.ImageField(upload_to='product_category/logo/big/',
                                 null=True,
                                 blank=True)
    logo_small = models.ImageField(upload_to='product_category/logo/small/',
                                   null=True,
                                   blank=True)
    parent_category = models.ForeignKey('ProductCategory',
                                        related_name='child_category',
                                        null=True,
                                        blank=True)
    features = models.ManyToManyField('ProductFeature',
                                      through='FeatureProductCategory')
    default_product = models.ForeignKey('Product',
                                        related_name='default_for_categories',
                                        null=True)

    class Meta:
        db_table = 'sm_product_category'
        verbose_name_plural = 'product categories'

    def __str__(self):
        return self.name


class Product(Auditable):
    """Products are final items in SM that customer can purchase
    ProductCategory describes families of Products

    code: The code of the Product
    name: The name of the Product
    category: ProductCategory - family of products this product belongs to
        we can get Vendor from this field. It have null=True because.
        referencing on product in ProductCategory.default_product so we have
        cycling referncing. To break it we made catagory null=True.
    display_name: Name that we would display to the user #TODO: not used yet
    vendor_sku: IMPORTANT the link between the product in our system and at vendor
        the code for this SKU/product at vendor (the link between the product in our system and at vendor
    version: the version of the ProductCategory this Product is from
    plan: describes the billin fewquency and commitment. See SubscriptionPlan
    type: SUBSCRIPTION vs ONE_SHOT
    tier_number: Maximum number of licenses in the Tier of this Product
    tier_name: String representing the Tier of this Product
    catalogs: many-to-many relationship with catalogs which can be used to determine the price

    """
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, null=True, related_name='products')
    display_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_sku = models.CharField(max_length=255, blank=True)
    version = models.ForeignKey('ProductVersion', null=True, related_name='products')
    plan = models.ForeignKey('ProductPlan', null=True, related_name='products')
    type = models.CharField(max_length=31, choices=ProductType.choices(), default=ProductType.SUBSCRIPTION.value)
    tier_number = models.IntegerField(default=-1)
    tier_name = models.CharField(max_length=255, blank=True, null=True)
    catalogs = models.ManyToManyField('Catalog', through='ProductCatalog')
    app_url = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True)
    unit_plural = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sm_product'

    @property
    def frequency_verbose(self):
        if self.plan == SubscriptionPlan.ANNUAL_YEARLY:
            return "yearly"
        else:
            return "monthly"

    @property
    def monthly(self):
        return self.plan == SubscriptionPlan.FLEX_PREPAID

    @property
    def unit_verbose(self):
        if self.tier_number == -1:
            return 'user'
        else:
            return 'pack'

    @property
    def commitment(self):
        return _('1 year') if not self.monthly else _('1 month')

    def get_commitment_days(self, start_date=None):
        if start_date is None:
            start_date = timezone.now()

        if self.monthly:
            total_seconds = (start_date + relativedelta(months=1) - start_date).total_seconds()
        else:
            total_seconds = (start_date + relativedelta(years=1) - start_date).total_seconds()

        return int(round(total_seconds / 3600 / 24))

    def get_price(self, catalog):
        return ProductCatalog.objects.get(product=self, catalog=catalog).price


class OrderType(Enum):
    NEW = ('NEW', _('New'))
    ADD = ('ADD', _('Add'))
    UPGRADE = ('UPGRADE', _('Upgrade'))


class DisplayProduct(models.Model):
    '''
    Model to define displaying options for products on pricing page.

    product_category:
    current_product: Current user product that user have.
    type: type of buying action.
    displayed_product: define product to show if user have current_product.
    display: Define show this product with current product or not.
    enabled: display button 'buy'/'upgrade' active or disabled.
    highlighted: frontend will highlight this product like "Most favorite" or
        something like that.
    showcase_alternate: toggle showing of the alternate price and frequency in
        the big pricing area.
    show_small: toggle displaying of additional alternative price.
    '''

    product_category = models.ForeignKey('ProductCategory', null=True)
    current_product = models.ForeignKey('Product', related_name='current')
    type = models.CharField(
        max_length=50, blank=True, choices=OrderType.choices()
    )
    displayed_product = models.ForeignKey('Product', related_name='displayed')
    display = models.BooleanField(
        default=True,
        help_text=_('Show this product with current product')
    )
    enabled = models.BooleanField(
        default=True, help_text=_('Enable buy/upgrade button')
    )
    highlighted = models.BooleanField(
        default=False, help_text=_('Distinguish product from others')
    )
    showcase_alternate = models.BooleanField(
        default=True, help_text=_('Show alternative price and frequency in the '
                                  'big pricing area')
    )
    show_small = models.BooleanField(
        default=True, help_text=_('Show additional alternative price')
    )

    class Meta:
        db_table = 'sm_display_product'


class DefaultProductPlan(models.Model):
    current_product = models.ForeignKey('Product')
    users_limit = models.IntegerField()
    plan = models.ForeignKey('ProductPlan')

    class Meta:
        db_table = 'sm_default_product_plan'

    def __str__(self):
        return '{} - user limit: {}'.format(self.current_product.name,
                                            self.users_limit)


class Catalog(Auditable):
    name = models.CharField(max_length=255, unique=True)
    products = models.ManyToManyField('Product', through='ProductCatalog')
    default = models.BooleanField(default=False)
    oid = models.IntegerField(default=0)  # Compatible with GSC

    def product_count(self):
        return self.products.count()

    def __str__(self):
        return self.name

    # find tiers that user can add licenses
    def get_available_tiers(self, version, plan, minimum_tier_number):
        # tier number should greater than 0
        assert minimum_tier_number > 0
        tiers = []
        for product in self.product_set.filter(
                version=version,
                plan=plan,
                tier_number__gte=minimum_tier_number).order_by('tier_number'):
            product_catalog = ProductCatalog.objects.get(product=product, catalog=self)
            tier = Tier()
            tier.price = product_catalog.price
            tier.product = product

            tier.high = product.tier_number
            tier.per_user = product_catalog.per_user
            tier.self_service = product_catalog.self_service

            tiers.append(tier)

        return tiers

    def get_tier(self, number, **filters):
        """
        :rtype: Tier
        """
        version = filters.get('version')
        if not (version is None or isinstance(version, ProductVersion)):
            filters['version'] = ProductVersion.objects.get(codename=version)

        plan = filters.get('plan')
        if not (plan is None or isinstance(plan, ProductPlan)):
            filters['plan'] = ProductPlan.objects.get(codename=plan)

        products = self.products.filter(**filters)

        if number > 0:
            products = products.filter(tier_number__gt=0)
        else:
            products = products.filter(tier_number=-1)

        if products.count() == 0:
            raise ValueError(
                'No product with tier_number {}, found in catalog "{}" with '
                'filter parameters {}'
                .format(number, self.name, filters)
            )

        tier = Tier()

        for product in products.filter().order_by('tier_number').all():
            product_catalog = ProductCatalog.objects.get(product=product, catalog=self)
            tier.high = product.tier_number
            tier.product = product
            tier.price = product_catalog.price
            tier.per_user = product_catalog.per_user
            tier.self_service = product_catalog.self_service
            if number <= product.tier_number:
                break
            else:
                tier.low = product.tier_number + 1
        return tier

    class Meta:
        db_table = 'sm_catalog'


class ProductCatalog(models.Model):
    product = models.ForeignKey('Product')
    catalog = models.ForeignKey('Catalog')
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                default=decimal.Decimal(0.0))
    per_user = models.BooleanField(default=False)
    self_service = models.BooleanField(default=False)
    alternate_price = models.DecimalField(max_digits=10,
                                          decimal_places=2,
                                          default=decimal.Decimal(0.0),
                                          null=True)
    minimal_order = models.DecimalField(max_digits=10,
                                        decimal_places=2,
                                        default=decimal.Decimal(0.0),
                                        null=True)

    def __str__(self):
        return " - ".join([self.catalog.name, self.product.name])

    class Meta:
        db_table = 'sm_product_catalog'
        unique_together = (('product', 'catalog'),)


# Deprecated
class PromotionCode(Auditable):
    catalog = models.ForeignKey('Catalog', related_name="promotion_codes")
    code = models.CharField(max_length=255, unique=True)
    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(blank=True, null=True)  # null for never ends

    def __str__(self):
        return ' - '.join([self.catalog.name, self.code])

    class Meta:
        db_table = 'sm_promotion_code'


class DiscountCode(Auditable):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=255, unique=True)
    amount = models.FloatField(default=0)
    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(blank=True, null=True)  # null for never ends

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sm_discount_code'


class SubscriptionPaymentMethod(Enum):
    PAYPAL_AUTO = ('PAYPAL_AUTO', _('Paypal auto'))
    PAYPAL_PREAPPROVED = ('PAYPAL_PREAPPROVED', _('Paypal preapproved'))
    PAYPAL_MANUAL = ('PAYPAL_MANUAL', _('Paypal manual'))
    OFFLINE = ('OFFLINE', _('Offline'))


class SubscriptionStatus(Enum):
    ACTIVE = ('ACTIVE', _('Active'))
    INACTIVE = ('INACTIVE', _('Inactive'))
    DRAFT = ('DRAFT', _('Draft'))
    DETECTED = ('DETECTED', _('Detected'))


class InvoiceStatus(Enum):
    OPEN = ('OPEN', _('Open'))
    PAID = ('PAID', _('Paid'))
    CANCELLED = ('CANCELLED', _('Cancelled'))
    OVERDUE = ('OVERDUE', _('OVERDUE'))
    PARTIALLY_PAID = ('PARTIALLY_PAID', _('Partially paid'))


class OrderStatus(Enum):
    CREATED = ('OPEN', _('Open'))
    CANCELLED = ('CANCELLED', _('Cancelled'))
    DELIVERED = ('DELIVERED', _('Delivered'))
    APPROVED = ('APPROVED', _('Approved'))
    INVOICE_SENT = ('INVOICE_SENT', _('Invoice sent'))
    PAID = ('PAID', _('Paid'))
    RENEWING = ('RENEWING', _('Renewing'))
    REFUNDED = ('REFUNDED', _('Refunded'))
    DRAFT = ('DRAFT', _('Draft'))


class RenewalOption(Enum):
    RENEW = ('RENEW', _('Renew'))
    FLEX = ('FLEX', _('Flex'))
    REDUCE = ('REDUCE', _('Reduce'))
    CANCEL = ('CANCEL', _('Cancel'))


class VendorStatus(Enum):
    EVAL = ('EVAL', 'EVAL')
    PAID = ('PAID', 'PAID')
    EXPIRED = ('EXPIRED', 'EXPIRED')
    EXPIRED_EVAL = ('EXPIRED_EVAL', 'EXPIRED_EVAL')
    EXPIRED_PAID = ('EXPIRED_PAID', 'EXPIRED_PAID')
    UNINSTALLED_EVAL = ('UNINSTALLED_EVAL', 'UNINSTALLED_EVAL')
    UNINSTALLED_PAID = ('UNINSTALLED_PAID', 'UNINSTALLED_PAID')
    UNINSTALLED_EXPIRED = ('UNINSTALLED_EXPIRED', 'UNINSTALLED_EXPIRED')
    # Google statuses (not used)
    ACTIVE = ('ACTIVE', 'ACTIVE')
    BILLING_ACTIVATION_PENDING = ('BILLING_ACTIVATION_PENDING', 'BILLING_ACTIVATION_PENDING')
    CANCELLED = ('CANCELLED', 'CANCELLED')
    PENDING = ('PENDING', 'PENDING')
    SUSPENDED = ('SUSPENDED', 'SUSPENDED')


class VendorConsole(Enum):
    EC = ('econsulting.fr', _('EConsulting'))
    CA = ('canada.gappsexperts.com', _('Canada Gapps'))
    MB = ('mybonobo.info', _('My bonobo'))


class SubscriptionOrderAddStrategy(Enum):
    PRORATE = ('PRORATE', _('Prorate'))
    EXTEND = ('EXTEND', _('Extend'))


class SubscriptionOrderUpgradeStrategy(Enum):
    REFUND = ('REFUND', _('Refund'))
    EXTEND = ('EXTEND', _('Extend'))


class Subscription(Auditable):
    """
    name: Type of the subscription can be "<Product type> for cusomter.name"
    order: FK that links the subscription with the initial order.
        (first access to checkout page) that was made for that subscription.
    customer:
    invoiced_customer: This is the customer who is going to receive and pay the invoices.
        They can be different from the customer. For instance :
        If a reseller ‘reseller.com’ pays for his customer ‘domain.com’.
        The subscription’s customer will be domain.com and the invoiced_customer will be reseller.com.
    product: FK to product table, used to see what the customer is subscribing to.
    catalog: It is the price list that is linked to this subscription.
        Then every time we will try to charge the customer for this product, we will check
        in the matching catalog table, what the price for this product is.
    trial: This subscription is in evaluation?
    parent_subscription: for nesting subscriptions, not used at the moment
    domain: The G Suite domain name of the customer. Attention ! When a @gmail.com user is registering,
        then the domain will be username__gmail.com. (username@gmail.com)
    payment_method: This field is used to say if the customer is offline or not.
        Currently when the subscription is created, it is populated by default to “PAYPAL_AUTO”,
        which will remain the same for ever. Sometime, support team sets this field to “Offline” manually.
        When a subscription is “Offline”, then the renewals and expiry crons will ignore it.
    trusted: Means that if the customer does not pay, we will not cancel their subscription.
    status: It is always set to “Active”, meaning that the subscription is supposed to be taken by the
        renewal crons and to show in the subscriptions page.
    licenses: Number of licenses that SM is providing to the user.
    max_cap: This is a limit that we do fix to prevent the customer to add in SM
        too many licences above a certain threshold.
    currency: This is the currency that will be used to create the orders related to this subscription
        (renewals, add, upgrade).
        The logic is as follow :
            - A customer wants to order a new subscription : The order will take the currency of the policy.
            - When the order is placed, then the subscription takes the currency of the order.
            - Whenever a customer orders something from this subscription (adding licences, ugrade, renewals),
              then these orders will take the currency of the subscription.
    saw_price: It means that the customer opened the pricing page at least once.
    install_date: This is the date when it was created in GSC.
        It is used for legacy GSC6 customers that were migrated to SM.
        We don’t really need it now. Since we have vendor_creation_date that should be populated when
        the vendor sends us this information.
    start_plan_date: Currently it is populated when the EVAL subscription is started in SM and updated
        when the paid plan starts.
    start_billing_date: Same as above. Should not exist.
    plan: This information contains the frequency and the commitment of the subscription.
        It does not need to be here because this information is specific to the product.
        Ideally we should remove this field and rely only on the product plan.
    renewal_option: It defines what will happen when we reach the subscription.expiry_date.
        If “Cancel”, it will contact the vendor to stop their service.
        If renew, it will renew it through the renewal cron.
    expiry_date: It is the date when the subscription will expire. It will be used by the crons to
        know when to renew or when to expire a subscription.
    next_invoice_date: It should be when the subscription will be billed again.
        It can be :
            expiry - 7 days for the flex_prepaid
            expiry - 60 days for the annual_yearly
            Last invoice “To_Date” in other cases
    billable_licenses:  This is the number of users in the customers’ G Suite domain.
        For Google Subscription, just synchronize with the value of “Vendor_licences”.
    billing_cycle: define when we should charge customer.
    add_order: when someone orders more licences to an existing subscription
        there are 2 possibilities:
        - either subscription.add_order is prorated, then we will charge the
            customer a prorated price till the end of the current billing_cycle.
        - or we charge the full price for these extra licences, but we will
            extend the subscription expiry as a compensation.
    upgrade_order: strategy similar to add_order but for case when we upgrading licenses.
    vendor_licenses: This is the number of licences of the product that the customer can use.
    vendor_status: This is the status of the customer’s account on the vendor side.
        For instance :
            GSC will have the following statuses:
            EVAL
            PAID
            EXPIRED_PAID
            EXPIRED_EVAL
            UNINSTALLED_PAID
            UNINSTALLED_EVAL
            Google will have the following statuses:
            ACTIVE
            BILLING_ACTIVATION_PENDING
            CANCELLED
            PENDING
            SUSPENDED
    sync_with_vendor: This field is to decide if we want all the changes happening on the vendor side
        to be synchronized with the SM subscription. No feature is using it for the moment.
    vendor_customer_id: This field is to store the ID of the customer on the vendor’s side.
    Vendor_subscription: This field should store the ID of the subscription on the vendor’s side.
    Vendor_product: This is the product that we are buying from the vendor. This is linked to our product table.
    vendor_trial: Indicates if the product is in evaluation on the vendor’s side.
    vendor_plan: Indicates the plan as it is captured from the vendor side (For Google : Annual, Flexible etc.)
    vendor_version: Indicates the product version as it is captured from the vendor side.
    vendor_renewal_option: Indicates the product version as it is captured from the vendor side.
    vendor_renewal_data: (typo for Date) :Not used for the moment.
    vendor_creation_date: Indicates the subscription creation date as it is captured from the vendor side.
    vendor_max_cap: Indicates the maximum adding capacity that a customer can add by himself on vendor’s side.
    bank_auth_id: Not used or needed at all.
    payment_gateway: This field indicates what was the last payment gateway that the customer used to pay
        those subscriptions (Paypal, Braintree, Offline invoice etc.)
    cancelled_by_user: This field is set to TRUE when the customer cancels their subscription through the
        “My Subscription” page.
    paypal_failure: This is a field that we used last year to detect what domained renewed without paying.
        We are not using it anymore.

    @property
    unbound: True when SM is not having any part in the contract and this Subscription is just describing
        the vendor agreement with the customer. False when SM is reselling this subscription
    """
    name = models.CharField(max_length=511)
    order = models.ForeignKey('Order', blank=True, null=True)
    customer = models.ForeignKey('Customer')
    invoiced_customer = models.ForeignKey(
        'Customer',
        related_name='invoiced_subscriptions',
        blank=True,
        null=True
    )  # same as customer by default
    product = models.ForeignKey('Product')
    catalog = models.ForeignKey('Catalog')
    trial = models.BooleanField(default=True)
    parent_subscription = models.ForeignKey(
        'Subscription',
        related_name='children',
        blank=True,
        null=True
    )
    domain = models.CharField(blank=True, null=True, max_length=255)
    payment_method = models.CharField(
        choices=SubscriptionPaymentMethod.choices(),
        default=SubscriptionPaymentMethod.PAYPAL_AUTO.value,
        max_length=63,
        blank=True
    )
    trusted = models.BooleanField(default=False)
    status = models.CharField(
        choices=SubscriptionStatus.choices(),
        default=SubscriptionStatus.ACTIVE.value,
        max_length=31
    )
    licenses = models.IntegerField(null=True, blank=True)
    max_cap = models.IntegerField(null=True, blank=True)
    currency = models.CharField(max_length=31, default='USD')
    saw_price = models.BooleanField(default=False)
    install_date = models.DateTimeField(auto_now_add=True)
    start_plan_date = models.DateTimeField(blank=True, null=True)
    # TODO: remove because start_billing_date is not used
    start_billing_date = models.DateTimeField(blank=True, null=True)
    plan = models.ForeignKey(
        'ProductPlan',
        related_name='subscriptions',
        blank=True,
        null=True
    )
    renewal_option = models.CharField(
        choices=RenewalOption.choices(),
        default=RenewalOption.CANCEL.value,
        max_length=31,
        blank=True
    )
    expiry_date = models.DateTimeField(null=True, blank=True)
    next_invoice_date = models.DateTimeField(blank=True, null=True)
    billable_licenses = models.IntegerField()  # licences that will be billed on next invoice
    billing_cycle = models.CharField(
        max_length=12,
        choices=BillingCycleEnum.choices()
    )
    billing_cycle_start = models.DateTimeField(blank=True, null=True)
    billing_cycle_end = models.DateTimeField(blank=True, null=True)
    add_order = models.CharField(
        choices=SubscriptionOrderAddStrategy.choices(),
        max_length=7
    )
    upgrade_order = models.CharField(
        choices=SubscriptionOrderUpgradeStrategy.choices(),
        max_length=6
    )

    sync_with_vendor = models.BooleanField(default=False)  # old vendor fields
    vendor_licenses = models.IntegerField()  # licences that are on app currently
    vendor_status = models.CharField(
        choices=VendorStatus.choices(),
        default=VendorStatus.EVAL.value,
        max_length=31,
        blank=True
    )
    vendor_console = models.CharField(
        max_length=255,
        choices=VendorConsole.choices(),
        blank=True
    )
    vendor_users = models.IntegerField(null=True, blank=True)
    vendor_customer_id = models.CharField(max_length=63, blank=True, null=True)
    vendor_subscription = models.CharField(max_length=55, blank=True, null=True)
    vendor_product = models.ForeignKey(
        'Product',
        related_name="buyer_subscription_set",
        blank=True,
        null=True
    )
    vendor_trial = models.BooleanField(default=False)
    vendor_plan = models.ForeignKey(
        'ProductPlan',
        related_name='vendor_subscription_set',
        blank=True,
        null=True
    )
    vendor_version = models.CharField(max_length=63, blank=True, null=True)
    vendor_renewal_option = models.CharField(
        max_length=63,
        blank=True,
        null=True
    )
    vendor_renewal_data = models.DateTimeField(blank=True, null=True)
    vendor_creation_date = models.DateTimeField(blank=True, null=True)
    vendor_max_cap = models.IntegerField(blank=True, null=True)
    vendor_minimum_transfer = models.IntegerField(blank=True, null=True)
    vendor_commitment_starts = models.DateTimeField(null=True, blank=True)
    vendor_commitment_ends = models.DateTimeField(null=True, blank=True)
    vendor_trial_ends = models.DateTimeField(null=True, blank=True)
    promotion_banner = models.IntegerField(blank=True, null=True)

    # todo: Bank Authorization ID (FK)
    bank_auth_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Bank Authorization ID'
    )

    payment_gateway = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="",
        verbose_name="Payment gateway",
        choices=(
            ("Braintree GAE", "Braintree GAE"),
            ("Paypal GAE", "Paypal GAE"),
            ("Paypal GSC", "Paypal GSC"),
            ("Paypal EC", "Paypal EC"),
            ("Invoice GAE", "Invoice GAE"),
            ("Invoice EC", "Invoice EC"),
            ("Internal domain", "Internal domain"),
            ("paid one time", "paid one time"),
        )
    )
    cancelled_by_user = models.BooleanField(default=False)
    paypal_failure = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def expired(self):
        return self.expiry_date and self.expiry_date < timezone.now()

    @property
    def cancelled(self):
        return self.renewal_option == RenewalOption.CANCEL

    @property
    def paid(self):
        return self.vendor_status in [VendorStatus.PAID,
                                      VendorStatus.UNINSTALLED_PAID]

    @property
    def is_eval(self):
        return self.vendor_status in [
            VendorStatus.EVAL,
            VendorStatus.EXPIRED_EVAL,
            VendorStatus.UNINSTALLED_EVAL
        ]

    def get_last_payment_amount(self):
        last_payment_amount = 0
        if self.paid:
            product_catalog = ProductCatalog.objects.get(
                catalog=self.catalog,
                product=self.product
            )  # subscription.order.sub_total  # should use sub_total to avoid discount problem

            if self.product.tier_number > 0:
                last_payment_amount = product_catalog.price
            else:
                last_payment_amount = product_catalog.price * self.vendor_licenses
        return last_payment_amount

    @property
    def renewal_date(self):
        tomorrow = timezone.now() + relativedelta(days=1)
        if self.product.monthly:
            return max(tomorrow, self.expiry_date + relativedelta(days=-7))
        else:
            return max(tomorrow, self.expiry_date + relativedelta(days=-60))

    @property
    def cost(self):
        if self.product:
            catalog = ProductCatalog.objects.get(product=self.product, catalog=self.catalog)
            if self.product.tier_number > 0:
                return catalog.price
            return catalog.price * self.vendor_licenses
        return 0

    @property
    def unbound(self):
        if self.status in [SubscriptionStatus.DRAFT,
                           SubscriptionStatus.DETECTED]:
            return True
        else:
            return False

    class Meta:
        db_table = 'sm_subscription'
        # unique_together = ('customer', 'product')


def get_payment_id(order):
    bt_tx = BraintreeTransaction.objects.filter(order=order).first()
    if bt_tx:
        assert isinstance(bt_tx, BraintreeTransaction)
        return "braintree:" + bt_tx.bt_id + ":" + str(bt_tx.id)
    else:
        paypal_tx = PaypalTransaction.objects.filter(order=order).first()
        if paypal_tx:
            assert isinstance(paypal_tx, PaypalTransaction)
            return "paypal:" + paypal_tx.profile_id + "_" + paypal_tx.txn_id + ":" + str(paypal_tx.id)


def get_first_payment_order(customer):
    order = Order.objects.filter(
        status=OrderStatus.PAID, customer=customer).order_by('date').first()
    if order:
        assert isinstance(order, Order)
        return order


def get_last_payment_order(customer):
    order = Order.objects.filter(
        status=OrderStatus.PAID, customer=customer).order_by('-date').first()
    if order:
        assert isinstance(order, Order)
        return order


class Invoice(Auditable):
    customer = models.ForeignKey('Customer')
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    conditions = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    currency = models.CharField(max_length=31, default='USD')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    tax = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=InvoiceStatus.choices(), default=InvoiceStatus.OPEN.value, max_length=31)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sm_invoice'


class InvoiceDetail(models.Model):
    invoice = models.ForeignKey('Invoice', related_name="details")
    product = models.ForeignKey('Product', related_name="invoice_details")
    subscription = models.ForeignKey('Subscription', related_name="invoice_details")
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField(default=1)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return " - ".join([self.invoice.name, self.product.name])

    class Meta:
        db_table = 'sm_invoice_detail'


# created after Customer is created
class Financial(Auditable):
    customer = models.ForeignKey("Customer")
    currency = models.CharField(max_length=31, default="USD")
    total_paid = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    total_invoiced = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    balance = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    status = models.CharField(max_length=255, blank=True, null=True)

    # payments
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    bank_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    bank_authroization_id = models.CharField(max_length=255, blank=True, null=True)
    payment_description = models.TextField(blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.customer.name

    class Meta:
        db_table = 'sm_financial'


class Order(Auditable):
    customer = models.ForeignKey('Customer')
    name = models.CharField(max_length=255)  # required
    date = models.DateTimeField(auto_now_add=True)
    conditions = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    currency = models.CharField(max_length=31, default='USD')
    discount = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    tax = models.DecimalField(max_digits=10, default=decimal.Decimal(0.0), decimal_places=2)
    status = models.CharField(choices=OrderStatus.choices(),
                              default=OrderStatus.CREATED.value,
                              max_length=31)
    comment = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def total(self):
        return (self.sub_total - self.sub_discount - self.discount) * (
                self.tax + 1)

    @property
    def sub_total(self):
        return sum([detail.sub_total or 0 for detail in self.details.all()])

    @property
    def sub_discount(self):
        return sum([detail.discount or 0 for detail in self.details.all()])

    class Meta:
        db_table = 'sm_order'


class OrderDetailType(Enum):
    TRANSFER = ('TRANSFER', 'Transfer')
    NEW = ('NEW', _('New'))
    ADD = ('ADD', _('Add'))
    UPGRADE = ('UPGRADE', _('Upgrade'))
    REFUND = ('REFUND', _('Refund'))
    RENEW = ('RENEW', _('Renew'))


class OrderDetail(models.Model):
    order = models.ForeignKey('Order', related_name="details")
    product = models.ForeignKey('Product', related_name='order_details')
    catalog = models.ForeignKey('Catalog', related_name='order_details')
    subscription = models.ForeignKey('Subscription',
                                     related_name='order_details',
                                     null=True,
                                     blank=True)
    description = models.TextField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     default=decimal.Decimal(0.0))
    amount = models.IntegerField(default=1)
    sub_total = models.DecimalField(max_digits=10,
                                    decimal_places=2,
                                    null=True)  # TODO change to required
    discount = models.DecimalField(max_digits=10,
                                   default=decimal.Decimal(0.0),
                                   decimal_places=2)
    minimal_quantity = models.BooleanField(default=True)
    status = models.CharField(choices=OrderStatus.choices(),
                              default=OrderStatus.CREATED.value,
                              max_length=31,
                              blank=True)
    type = models.CharField(max_length=31,
                            blank=True,
                            choices=OrderDetailType.choices())
    tax = models.DecimalField(max_digits=10,
                              decimal_places=2,
                              null=True,
                              blank=True)
    from_date = models.DateTimeField(null=True, blank=True)
    to_date = models.DateTimeField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    extension = models.DecimalField(max_digits=10,
                                    decimal_places=2,
                                    null=True,
                                    blank=True)
    refunded_amount = models.DecimalField(max_digits=10,
                                          decimal_places=2,
                                          null=True,
                                          blank=True)
    minimal_order = models.DecimalField(max_digits=10,
                                        decimal_places=2,
                                        null=True,
                                        blank=True)

    def __str__(self):
        return " - ".join((self.order.name, self.product.name))

    @property
    def total(self):
        return self.sub_total - self.discount

    class Meta:
        db_table = 'sm_order_detail'


class ProfileClazz(models.Model):
    product_clazz = models.CharField(max_length=31)  # GSC/MAPI etc..
    profile = models.ForeignKey("Profile")

    class Meta:
        db_table = "sm_profile_clazz"


class VendorProfileClazz(models.Model):
    product_clazz = models.CharField(max_length=31)
    vendor_profile = models.ForeignKey("VendorProfile")

    class Meta:
        db_table = "sm_vendor_profile_clazz"


class PaypalBillingPlan(Auditable):
    product_catalog = models.ForeignKey("ProductCatalog", related_name='paypal_plan')
    paypal_id = models.CharField(max_length=255, verbose_name="Plan id")

    class Meta:
        db_table = "sm_paypal_billing_plan"


class PaypalTransaction(Auditable):
    order = models.ForeignKey(Order)
    profile_id = models.CharField(max_length=63)
    txn_id = models.CharField(max_length=63, null=True, blank=True)
    payment_time = models.DateTimeField()

    class Meta:
        db_table = 'sm_paypal_transaction'


class BraintreeCustomer(models.Model):
    user = models.ForeignKey('User')
    bt_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'sm_gt_customer'


class BraintreeSubscription(Auditable):
    subscription = models.ForeignKey("Subscription", related_name="bt")
    bt_id = models.CharField(max_length=255, verbose_name="Braintree Id")
    status = models.CharField(max_length=255,
                              default=braintree.Subscription.Status.Active)
    detail = models.TextField()
    cancelled = models.BooleanField(default=False)

    class Meta:
        db_table = "sm_bt_subscription"


class BraintreeTransaction(Auditable):
    order = models.ForeignKey("Order", related_name="bt_transaction")
    status = models.CharField(max_length=255, default="Not Completed")
    completed_date = models.DateTimeField()
    bt_id = models.CharField(max_length=255, default="")
    error = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "sm_bt_transaction"

    def __str__(self):
        return "bt_tx:%s" % self.bt_id


class Tier(object):
    def __init__(self):
        self.low = 1
        self.high = None
        self.product = None
        self.price = None
        self.per_user = None
        self.self_service = None

    def scope(self):
        return "%s - %s" % (self.low, self.high)


class ZohoCustomerRecord(models.Model):
    customer = models.OneToOneField("Customer")
    lead_id = models.CharField(max_length=255, blank=True, null=True)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    potential_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "%s:%s:%s:%s" % (self.customer.name, self.lead_id, self.account_id, self.potential_id)

    class Meta:
        db_table = 'sm_zoho_customer_record'


class ZohoContactRecord(models.Model):
    user = models.OneToOneField("User")
    contact_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "%s:%s" % (self.user.customer.name, self.contact_id)

    class Meta:
        db_table = 'sm_zoho_contact_record'


class FailedTransaction(models.Model):
    order = models.ForeignKey('Order', related_name="failed_transactions")
    date = models.DateTimeField()
    potential_id = models.CharField(max_length=63, blank=True, null=True)
    error = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'sm_failed_transactions'

    def __str__(self):
        return 'failed_transaction:%s'


class Currency(Enum):
    USD = ('USD', _('American Dollars'))
    EUR = ('EUR', _('Euro'))
    CAD = ('CAD', _('Canadian Dollars'))


# TODO Remove
class Policy(models.Model):
    # Fields to search by
    product_category = models.ForeignKey(ProductCategory, max_length=255, null=True)
    per_user = models.BooleanField()
    customer_type = models.CharField(choices=CustomerType.choices(), max_length=255, blank=True)
    customer_region = models.CharField(max_length=255, blank=True)
    offline_customer = models.NullBooleanField(null=True)
    customer_country = models.CharField(max_length=255, blank=True)
    order_type = models.CharField(max_length=255, blank=True)

    # Fields for writing logic
    product = models.ForeignKey('Product', null=True, blank=True)
    currency = models.CharField(choices=Currency.choices(), max_length=15, blank=True)
    catalog = models.ForeignKey('Catalog', null=True, blank=True)
    vendor_console = models.CharField(choices=VendorConsole.choices(), max_length=255, blank=True)
    minimal_quantity = models.IntegerField(null=True, blank=True)
    tax_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'sm_policy'
        verbose_name_plural = 'policies'


class Country(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True)
    currency = models.CharField(max_length=10, default='USD')
    continent = models.CharField(max_length=35)
    trans = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'sm_country'
        verbose_name_plural = 'countries'

    @property
    def translation(self):
        return self.trans if not None else self.name


class VendorField(models.Model):
    vendor = models.ForeignKey('Vendor')
    vendor_name = models.CharField(max_length=255)
    sm_name = models.CharField(max_length=255)

    def __str__(self):
        return '{}_{}'.format(self.vendor.name, self.vendor_name)

    class Meta:
        db_table = 'sm_vendor_fields'


class VendorValue(models.Model):
    field = models.ForeignKey('VendorField')
    vendor_value = models.CharField(max_length=255)
    sm_value = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'sm_vendor_values'


class ResellerTempAccount(models.Model):
    t_stamp = models.DateTimeField(auto_now_add=True)
    zoho_lead_id = models.CharField(max_length=255, db_index=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=255, blank=True, default='')
    state = models.CharField(max_length=255, blank=True, default='')
    zip = models.CharField(max_length=255, blank=True, default='')
    country = models.CharField(max_length=255, blank=True, default='')
    message = models.CharField(max_length=1024, blank=True, default='')
    lead_source = models.CharField(max_length=1024, blank=True, default='')
    web_form = models.CharField(max_length=1024, blank=True, default='')
    lang = models.CharField(max_length=1024, blank=True, default='')
