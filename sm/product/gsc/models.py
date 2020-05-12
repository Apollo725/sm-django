from __future__ import absolute_import

import datetime
import logging

from django.conf import settings
from requests import RequestException

from django.dispatch import receiver

from sm.core.models import *
from sm.test.models import *
from sm.core.signals import subscription_updated, customer_updated_by_admin
from django.db.models.signals import pre_save
from dateutil.relativedelta import relativedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

PRODUCT_CLAZZ = 'GSC'

RESELLER = 'reseller'


def get_gsc_product_category():
    return ProductCategory.objects.get(code='GSC')


def get_vendor_profile(customer):
    """

    :rtype: sm.core.models.VendorProfile
    :except: VendorProfileClazz.DoesNotExist
    """
    return VendorProfileClazz.objects.get(
        product_clazz=PRODUCT_CLAZZ, vendor_profile__customer=customer).vendor_profile


def try_to_get_vendor_profile(customer):
    rel = VendorProfileClazz.objects.filter(
        product_clazz=PRODUCT_CLAZZ, vendor_profile__customer=customer).first()
    if rel:
        return rel.vendor_profile


def get_default_catalog(customer_id=None):
    catalogs = Catalog.objects.filter(default=True)

    if len(catalogs) == 0:
        raise Catalog.DoesNotExist("Default catalog doesn't exist!")

    # ab_test, SM-33
    if customer_id:
        size = catalogs.count()
        index = (customer_id - 1) % size
        return catalogs[index]
    else:
        return catalogs.first()


def get_default_tier(catalog, number_of_users):
    return catalog.get_tier(
        number_of_users,
        version=ProductVersionEnum.PRO,
        plan=SubscriptionPlan.ANNUAL_YEARLY)


def get_tiers(catalog, number_of_users):
    return dict(
        yearly=dict(
            pro=get_default_tier(catalog, number_of_users),
            enterprise=catalog.get_tier(
                number_of_users,
                version=ProductVersionEnum.ENTERPRISE,
                plan=SubscriptionPlan.ANNUAL_YEARLY),
            basic=catalog.get_tier(
                5,
                version=ProductVersionEnum.BASIC,
                plan=SubscriptionPlan.ANNUAL_YEARLY
            )

        ),
        monthly=dict(
            pro=catalog.get_tier(
                number_of_users,
                version=ProductVersionEnum.PRO,
                plan=SubscriptionPlan.FLEX_PREPAID),
            enterprise=catalog.get_tier(
                number_of_users,
                version=ProductVersionEnum.ENTERPRISE,
                plan=SubscriptionPlan.FLEX_PREPAID),
            basic=catalog.get_tier(
                5, version=ProductVersionEnum.BASIC,
                plan=SubscriptionPlan.FLEX_PREPAID
            )
        )
    )


class SubscriptionManager(object):

    def __init__(self, customer):
        self.customer = customer

    @staticmethod
    def _get_default_product():
        product = Product.objects.filter(code=settings.DEFAULT_PRODUCT_CODE_TRIAL_SUBSCRIPTION).first()
        if product:
            return product
        else:
            raise Exception('You need to set default product code for trial subscription')

    def _create_eval_subscription(self):
        catalog = get_default_catalog(self.customer.id)
        vendor_profile = get_vendor_profile(self.customer)

        subscription = Subscription.objects.create(
            customer=self.customer,
            invoiced_customer=self.customer,
            catalog=catalog,
            product=self._get_default_product(),
            name="GSC for %s" % vendor_profile.name,
            domain=vendor_profile.name,
            billable_licenses=vendor_profile.users or 1,
            vendor_licenses=0,
            vendor_status=VendorStatus.EVAL,
            status=SubscriptionStatus.ACTIVE,
            currency=vendor_profile.currency,
            install_date=timezone.now(),
            expiry_date=calculate_eval_expiration_date(),
            start_plan_date=timezone.now(),
            plan=ProductPlan.objects.get(
                codename=SubscriptionPlan.ANNUAL_YEARLY
            ),
            vendor_plan=ProductPlan.objects.get(
                codename=SubscriptionPlan.ANNUAL_YEARLY
            ),
        )

        logger.info("subscription is created for %s, catalog: %s", subscription.name, catalog)

        return subscription

    def ensure_exists(self):
        subscription = self.get_subscription()

        # create eval subscription if not exist
        if not subscription:
            subscription = self._create_eval_subscription()
        return subscription

    def get_subscription(self):
        # type: () -> Subscription
        return Subscription.objects.filter(
            customer=self.customer,
            product__category=get_gsc_product_category()
        ).order_by('-modified_at').first()


def get_profile(customer):
    cls = ProfileClazz.objects.filter(
        profile__customer=customer,
        product_clazz=PRODUCT_CLAZZ
    ).first()

    if cls:
        return cls.profile
    return None


def add_catalog(oid, name, basic_price, price_list, default=False):
    catalog, _ = Catalog.objects.get_or_create({
        'default': default,
        'oid': oid
    }, **{
        'name': name
    })

    def create_product(tier_low, tier_high, version, plan, price):
        def _create_product(tier_low, tier_high, version, plan):
            return Product.objects.update_or_create(
                {
                    'name': 'GSC %s (%d-%d) Users (%s)' % (
                        version.codename.lower(), tier_low, tier_high, plan.name.lower()),
                    'version': version,
                    'plan': plan,
                    'type': ProductType.SUBSCRIPTION,
                    'tier_number': tier_high,
                    'tier_name': '%d - %d' % (tier_low, tier_high),
                    'category_id': 1
                }, **{
                    'code': 'gsc_%s_%s_%d-%s' % (
                        version.codename.lower(), tier_low, tier_high, plan.codename.lower())
                }
            )

        version = ProductVersion.objects.get(codename=version)
        plan = ProductPlan.objects.get(codename=plan)

        product, _ = _create_product(tier_low,
                                     tier_high,
                                     version,
                                     plan)

        ProductCatalog.objects.update_or_create(
            {
                'price': price,
                'alternate_price': 0,
                'minimal_order': 5,
            },
            catalog=catalog,
            product=product
        )

    def _create_product_per_user(version, plan, price):
        def _create_product(version, plan):
            return Product.objects.update_or_create(
                {
                    'name': 'GSC %s (%s)' % (
                        version.codename.lower(), plan.name.lower()),
                    'version': version,
                    'plan': plan,
                    'type': ProductType.SUBSCRIPTION,
                    'category_id': 1
                }, **{
                    'code': 'gsc_%s_%s' % (
                        version.codename.lower(), plan.codename.lower())
                }
            )

        version = ProductVersion.objects.get(codename=version)
        plan = ProductPlan.objects.get(codename=plan)

        product, _ = _create_product(version,
                                     plan)

        ProductCatalog.objects.update_or_create(
            {
                'price': price,
                'per_user': True,
                'self_service': True,
                'alternate_price': 0,
                'minimal_order': 5,
            },
            catalog=catalog,
            product=product
        )

    def _add_product(tier_low, tier_high, price):
        create_product(tier_low, tier_high, ProductVersionEnum.PRO, SubscriptionPlan.ANNUAL_YEARLY, price)
        create_product(tier_low, tier_high, ProductVersionEnum.PRO, SubscriptionPlan.FLEX_PREPAID, price / 10)
        create_product(tier_low, tier_high, ProductVersionEnum.ENTERPRISE, SubscriptionPlan.ANNUAL_YEARLY, price * 1.2)
        create_product(tier_low, tier_high, ProductVersionEnum.ENTERPRISE, SubscriptionPlan.FLEX_PREPAID, price / 10 * 1.2)

    low = 1
    for price in price_list:
        if not isinstance(price[0], ProductVersionEnum):  # filter tier price list
            high, price = price
            _add_product(low, high, price)
            low = high + 1

    create_product(1, 5, ProductVersionEnum.BASIC, SubscriptionPlan.ANNUAL_YEARLY, basic_price)
    create_product(1, 5, ProductVersionEnum.BASIC, SubscriptionPlan.FLEX_PREPAID, basic_price / 10)

    for price in price_list:
        if isinstance(price[0], str):  # filter tier price list
            version, yearly, monthly = price
            _create_product_per_user(version, SubscriptionPlan.ANNUAL_YEARLY, yearly)
            _create_product_per_user(version, SubscriptionPlan.FLEX_PREPAID, monthly)

    return catalog


def on_subscription_updated(sender, instance, force=False, async=True, **kwargs):
    """

    :type instance: Subscription
    """

    if settings.TESTING:
        return

    # SM-88
    if instance.vendor_status == VendorStatus.PAID:
        if instance.customer.type == CustomerType.PROSPECT:
            instance.customer.type = CustomerType.CUSTOMER
            instance.customer.save()
        elif instance.customer.type == CustomerType.RESOLD_PROSPECT:
            instance.customer.type = CustomerType.RESOLD_CUSTOMER
            instance.customer.save()

    from sm.product.gsc.app_api import update_license

    update_license(instance)
    from sm.product.gsc import zoho
    # noinspection PyBroadException
    try:
        zoho.update_account(instance.customer.get_communication_user(), async=async)
    except Exception:
        logger.exception("Failed to update account %s" % instance.customer)


def create_transaction_from_gsc(profile_id, txn_id, catalog_id, customer, tier):
    txn = PaypalTransaction.objects.filter(profile_id=profile_id).first()
    if txn:
        return txn

    catalog = Catalog.objects.get(oid=catalog_id)
    tier = catalog.get_tier(tier,
                            version=ProductVersionEnum.PRO,
                            plan=SubscriptionPlan.ANNUAL_YEARLY)

    product = tier.product

    order = Order.objects.create(
        customer=customer,
        name="GSC order for %s" % customer.name,
        status=OrderStatus.PAID)

    OrderDetail.objects.create(order=order,
                               product=product,
                               catalog=catalog,
                               sub_total=product.get_price(catalog))

    return PaypalTransaction.objects.create(
        order=order,
        profile_id=profile_id,
        txn_id=txn_id,
        payment_time=timezone.now()
    )


def remove_not_paid_order(sender, instance, **kwargs):
    assert isinstance(instance, Subscription)

    order_details = OrderDetail.objects.filter(
        order__customer=instance.customer,
        product__category=get_gsc_product_category(),
        subscription=SubscriptionManager(instance.customer).get_subscription(),
        order__status=OrderStatus.CREATED
    )

    for order_detail in order_details:
        order_detail.order.delete()


subscription_updated.connect(on_subscription_updated, Subscription)
subscription_updated.connect(remove_not_paid_order, Subscription)


def get_open_order_detail(customer):
    return OrderDetail.objects.filter(
        order__customer=customer,
        product__category=get_gsc_product_category(),
        subscription=SubscriptionManager(customer).get_subscription(),
        order__status=OrderStatus.CREATED
    ).order_by('-order__date').first()


def create_order(customer):
    return Order.objects.create(
        customer=customer,
        name="GSC order for %s" % customer.name,
        currency=get_vendor_profile(customer).currency,
        status=OrderStatus.CREATED,
        due_date=timezone.now() + relativedelta(hours=1),
    )


class RemainDays(object):
    def __init__(self, remain, total):
        if remain < 0:
            self.remain = 0
        else:
            self.remain = remain
        self.total = total

    def to_json(self):
        return {
            'remain': self.remain,
            'total': self.total
        }

    def __str__(self):
        import json
        return json.dumps(self.to_json())


def get_remaining_days(subscription):
    if not subscription.paid:
        return None
    else:
        plan = subscription.product.plan

        def calculation(relative_delta):
            today = timezone.now()
            # assert subscription.next_invoice_date.date() >= today.date()
            start_plan_date = subscription.expiry_date + relative_delta
            remain_days = (subscription.expiry_date - today).days
            total_days = (subscription.expiry_date - start_plan_date).days
            return RemainDays(remain_days, total_days)

        if plan == SubscriptionPlan.ANNUAL_YEARLY:
            return calculation(relativedelta(years=-1))
        elif plan == SubscriptionPlan.FLEX_PREPAID:
            return calculation(relativedelta(months=-1))
        raise ValueError("Can't calculate credits plan = %s", plan)


def is_braintree_subscription_valid(bt_id):
    import braintree.exceptions
    try:
        subscription = braintree.Subscription.find(bt_id)
        if subscription.status != braintree.Subscription.Status.Canceled:
            return True
    except braintree.exceptions.NotFoundError:
        pass

    return False


# calculate the expiration date for monthly/yearly payment
def calculate_expiration_date(start_date=None, monthly=False):
    if start_date is None:
        start_date = timezone.now()

    start_time = datetime.datetime(
        year=start_date.year, month=start_date.month, day=start_date.day,
        hour=4, tzinfo=timezone.utc)

    if monthly:
        return start_time + relativedelta(months=1, minutes=-10)
    else:
        return start_time + relativedelta(years=1, minutes=-10)


def calculate_eval_expiration_date(start_date=None):
    if not start_date:
        start_date = timezone.now()
    start_time = datetime.datetime(
        year=start_date.year, month=start_date.month, day=start_date.day,
        hour=4, tzinfo=timezone.utc)
    return start_time + relativedelta(days=15, minutes=-10)


def save_payment_method(customer_id, token):
    instance, created = BraintreePaymentMethod.objects.update_or_create(
        customer_id=customer_id,
        token=token
    )

    return instance


def enable_payment_method(token):
    """

    :type token: basestring
    """
    BraintreePaymentMethod.objects.filter(
        token=token
    ).update(succeed=True)

    logger.info("Payment method %s is enabled", token)


def disable_payment_method(token):
    """

    :type token: basestring
    """
    BraintreePaymentMethod.objects.filter(
        token=token
    ).update(succeed=False)

    logger.info("Payment method %s is disabled", token)


def find_payment_method(customer):
    """Find the payment method succeed to pay

    :type customer: Customer
    :rtype BraintreePaymentMethod
    """
    customer_id_list = ['sm_' + user.auth_user.username for user in customer.users.all()]
    method = BraintreePaymentMethod.objects.filter(
        customer_id__in=customer_id_list,
    ).order_by('-succeed', '-modified_at', '-default').first()
    return method


def calculate_total_paid(customer):
    order_details = OrderDetail.objects.filter(
        order__customer=customer,
        product__category=get_gsc_product_category(),
        order__status=OrderStatus.PAID
    )
    return sum([detail.total for detail in order_details])


def create_bt_transaction(order, transaction_id, error=""):
    status = "Completed" if (not error and transaction_id) else "Error"
    BraintreeTransaction.objects.create(
        order=order,
        bt_id=transaction_id,
        completed_date=timezone.now(),
        status=status,
        error=error
    )


def get_payment_methods_offline(customer):
    """Find the payment methods for this customer

    :type customer: Customer
    :rtype BraintreePaymentMethod
    """
    payment_methods = []
    customer_id_list = ['sm_' + user.auth_user.username for user in customer.users.all()]
    for customer_id in customer_id_list:
        user = User.objects.get(auth_user__username=customer_id[3:])
        bt_payment_methods = BraintreePaymentMethod.objects.filter(
            customer_id__in=customer_id_list,
        ).order_by('-succeed', '-modified_at', '-default')
        for payment_method in bt_payment_methods:
            payment_methods.append([payment_method, user, customer_id])
            logger.info("Found payment method for %s: %s", user,payment_method)
    return payment_methods


@receiver(pre_save, sender=Customer)
def before_customer_updated(sender, instance, **kwargs):
    customer = instance
    assert isinstance(customer, Customer)
    if customer.reseller_id:
        if customer.type == CustomerType.PROSPECT:
            customer.type = CustomerType.RESOLD_PROSPECT
    else:
        if customer.type == CustomerType.RESOLD_PROSPECT:
            customer.type = CustomerType.PROSPECT


def on_customer_updated_by_admin(sender, instance, **kwargs):
    from . import zoho
    assert isinstance(instance, Customer)
    logger.debug("customer %s is updated by admin, triggers zoho updating", instance)
    zoho.update_account(instance.get_communication_user())


customer_updated_by_admin.connect(on_customer_updated_by_admin)
