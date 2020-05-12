from __future__ import absolute_import

import logging

from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.utils.crypto import get_random_string

from sm.core.signals import customer_updated_by_admin, subscription_updated
from sm.product.google.models import GoogleTransferToken

from .forms import SelectProducts
from .models import *
from .utils.model_utils import create_display_products_from_product

logger = logging.getLogger(__name__)


class ProfileInline(admin.StackedInline):
    model = Profile


class VendorProfileInline(admin.StackedInline):
    model = VendorProfile


class CustomerAdminForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'

    exclude = []

    def __init__(self, *args, **kwargs):
        super(CustomerAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['communication_user'].queryset = User.objects.filter(customer=self.instance)


class CustomerAdmin(admin.ModelAdmin):
    form = CustomerAdminForm

    list_display = ('name', 'type', 'balance', 'created_at')
    inlines = [ProfileInline, VendorProfileInline]

    ordering = ('-created_at',)

    search_fields = ('name',)

    related_search_fields = {
        'reseller': ('name',),
    }

    raw_id_fields = ['communication_user', 'reseller']

    def save_form(self, request, form, change):
        obj = super(CustomerAdmin, self).save_form(request, form, change)
        customer_updated_by_admin.send(Customer, instance=obj)
        return obj


class UserAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'email', 'role', 'created_at')

    search_fields = ('name', 'email')
    ordering = ('-created_at',)

    raw_id_fields = ['customer', 'auth_user']


class CatalogInline(admin.StackedInline):
    model = Product.catalogs.through

    raw_id_fields = ["catalog"]


class ProductInline(admin.StackedInline):
    model = Catalog.products.through

    raw_id_fields = ["product"]


class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'tier_number', 'version', 'plan', 'type')
    search_fields = ('code', 'name')
    inlines = [CatalogInline]


class CatalogAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'oid')
    inlines = [ProductInline]
    search_fields = ('name', )

    actions = ['duplicate']

    def duplicate(modeladmin, request, queryset):
        catalogs = queryset.all()
        for catalog in catalogs:
            name = catalog.name
            catalog_id = catalog.id

            catalog.pk = None
            catalog.name = name + " (duplicated %s)" % get_random_string(2)
            catalog.oid = int(Catalog.objects.all().aggregate(Max('oid'))['oid__max']) + 1
            catalog.save()

            for product_catalog in ProductCatalog.objects.filter(catalog_id=catalog_id).all():
                product_catalog.pk = None
                product_catalog.catalog = catalog
                product_catalog.save()

    duplicate.short_description = 'Duplicate selected'


class PromotionCodeAdmin(admin.ModelAdmin):
    list_display = ('catalog', 'code', 'start_at', 'end_at')


class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_at', 'end_at')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'customer', 'product', 'catalog', 'trial', 'payment_method', 'renewal_option',
        'expiry_date', 'expired', 'billable_licenses', 'vendor_licenses', 'created_at', 'install_date',
        'payment_gateway'
    )

    search_fields = ('name', 'customer__name')
    ordering = ('-created_at',)
    exclude = ('next_invoice_date',)

    raw_id_fields = [
        'product',
        'catalog',
        'customer',
        'order',
        'invoiced_customer',
    ]

    def save_form(self, request, form, change):
        obj = super(SubscriptionAdmin, self).save_form(request, form, change)
        subscription_updated.send(Subscription, instance=obj)
        return obj


class SubscriptionProxy(Subscription):
    class Meta:
        proxy = True
        verbose_name = "Subscription View"
        verbose_name_plural = "Subscriptions View"


BRAINTREE_SUBSCRIPTION = 'https://{}.braintreegateway.com/merchants/{}/{}/{}'
PAYPAL_PROFILE_LINK = "https://{}.paypal.com/cgi-bin/webscr?cmd=_profile-recurring-payments&encrypted_profile_id={}"


def get_braintree_favicon():
    return '<img height="10px" src="https://www.braintreegateway.com/favicon.ico">'


def get_paypal_favicon():
    return '<img height="10px" src="https://www.paypalobjects.com/favicon.ico">'


def get_braintree_url(resource, resource_id):
    from django.conf import settings
    return BRAINTREE_SUBSCRIPTION.format(
        'www' if not settings.BRAINTREE_SANDBOX else 'sandbox',
        settings.BRAINTREE_MERCHANT_ID,
        resource,
        resource_id
    )


def get_paypal_url(profile_id):
    from django.conf import settings
    return PAYPAL_PROFILE_LINK.format(
        'www' if not settings.PAYPAL_IPN_SANDBOX else "sandbox",
        profile_id
    )


class SubscriptionProxyAdmin(admin.ModelAdmin):
    list_display = (
        'link_to_subscription',
        'link_to_customer',
        'status',
        'vendor_status',
        'product_version',
        '_plan',
        'vendor_licenses',
        'last_pay_amount',
        'expiry_date_f',
        'renewal_date_f',
        # 'link_to_payment_source',
        'payment_gateway',
        'payment_position',
        'first_payment_date',
        'first_payment_id',
        'last_payment_date',
        'last_payment_id',
        'last_payment_outcome',
        'total_revenue',
    )

    search_fields = ('name',)
    list_filter = (
        'vendor_status',
        'payment_gateway',
        'paypal_failure',
        'product__plan',
        'product__version'
    )
    ordering = ('-created_at',)

    def product_version(self, obj):
        if obj.product:
            return obj.product.version

    product_version.admin_order_field = 'product__version'

    def last_pay_amount(self, obj):
        if obj.order and obj.order.status == OrderStatus.PAID:
            return obj.order.total

    def renewal_date(self, obj):
        from dateutil.relativedelta import relativedelta
        from django.utils import timezone
        tomorrow = timezone.now() + relativedelta(days=1)
        if not obj.expiry_date:
            return None
        if not obj.cancelled:
            if obj.product.monthly:
                return max(tomorrow, obj.expiry_date + relativedelta(days=-7))
            else:
                if PaypalTransaction.objects.filter(order=obj.order).exists():
                    return max(tomorrow, obj.expiry_date)
                return max(tomorrow, obj.expiry_date + relativedelta(days=-60))

    def expiry_date_f(self, obj):
        expiry_date = obj.expiry_date
        if expiry_date:
            return obj.expiry_date.strftime('%Y-%m-%d')
        return ""

    expiry_date_f.allow_tags = True
    expiry_date_f.short_description = "Expiry Date"
    expiry_date_f.admin_order_field = 'expiry_date'

    def renewal_date_f(self, obj):
        renewal_date = self.renewal_date(obj)
        if renewal_date:
            return self.renewal_date(obj).strftime('%Y-%m-%d')
        return ""

    renewal_date_f.allow_tags = True
    renewal_date_f.short_description = "Renewal Date"

    def link_to_payment_source(self, obj):
        if obj.order:
            tx = PaypalTransaction.objects.filter(order=obj.order).order_by('-id').first()
            if tx:
                return '<a href="{}">{}</a> <a href="{}" target="_blank">{}</a>'.format(
                    reverse('admin:core_paypaltransaction_changelist') + "?id=" + str(tx.id),
                    tx.profile_id,
                    get_paypal_url(tx.profile_id),
                    get_paypal_favicon()
                )
            bt_transaction = BraintreeTransaction.objects.filter(
                order=obj.order, status="Completed").order_by('-completed_date').first()
            if bt_transaction:
                return '<a href="{}">{}</a> <a href="{}" target="_blank">{}</a>'.format(
                    reverse('admin:core_braintreetransaction_changelist') + "?id=" + str(bt_transaction.id),
                    bt_transaction.bt_id,
                    get_braintree_url("transactions", bt_transaction.bt_id),
                    get_braintree_favicon()
                )
            bt_sub = BraintreeSubscription.objects.filter(subscription=obj, cancelled=False).order_by('-id').first()
            if bt_sub:
                return '<a href="{}" target="_blank">{}</a> '.format(
                    get_braintree_url('subscriptions', bt_sub.bt_id), bt_sub.bt_id
                )

    link_to_payment_source.allow_tags = True
    link_to_payment_source.short_description = "Payment Source"

    def link_to_subscription(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:core_subscription_change',
                    args=[obj.id]), obj.name)

    link_to_subscription.allow_tags = True
    link_to_subscription.short_description = "Subscription"

    def link_to_customer(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:core_customer_change',
                    args=[obj.customer.id]), obj.customer.name)

    link_to_customer.allow_tags = True
    link_to_customer.short_description = "Customer"
    link_to_customer.admin_order_field = 'customer'

    def render_payment_link(self, payment_id):
        if not payment_id or payment_id == 'None':
            return ""
        payment_type, txn_id = payment_id.split(":")[:2]
        if payment_type == 'paypal':
            parts = txn_id.split('_')
            if len(parts) == 2:
                profile_id, txn_id = parts
            else:
                profile_id = parts[0]
                txn_id = ""
            return '<a href="{}" target="_blank">{}{}</a>'.format(
                get_paypal_url(profile_id),
                get_paypal_favicon(),
                txn_id
            )
        elif payment_type == 'braintree':
            return '<a href="{}" target="_blank">{} {}</a>'.format(
                get_braintree_url("transactions", txn_id),
                get_braintree_favicon(),
                txn_id,
            )

    def payment_position(self, obj):
        return obj.customer.payment_position

    def first_payment_date(self, obj):
        date = obj.customer.first_payment_date
        if date:
            return date.strftime(time_format)

    def first_payment_id(self, obj):
        return self.render_payment_link(
            obj.customer.first_payment_id
        )

    def last_payment_date(self, obj):
        date = obj.customer.last_payment_date
        if date:
            return date.strftime(time_format)

    def last_payment_id(self, obj):
        return self.render_payment_link(
            obj.customer.last_payment_id
        )

    def total_revenue(self, obj):
        return obj.customer.total_revenue

    def last_payment_outcome(self, obj):
        return obj.customer.last_payment_outcome

    first_payment_id.allow_tags = True
    last_payment_id.allow_tags = True

    def _plan(self, obj):
        if obj.product:
            return obj.product.plan
        else:
            return None

    _plan.admin_order_field = 'product__plan'
    _plan.short_description = 'Plan'


time_format = "%Y-%m-%d"


class InvoiceDetailInline(admin.StackedInline):
    model = InvoiceDetail


class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'name', 'due_date', 'discount', 'total', 'created_at'
    )
    inlines = [InvoiceDetailInline]

    search_fields = ('customer__name',)


class OrderDetailInline(admin.StackedInline):
    model = OrderDetail

    raw_id_fields = [
        'product', 'catalog', 'subscription'
    ]


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'name', 'due_date', 'discount', 'total', 'created_at', 'status'
    )
    inlines = [OrderDetailInline]
    ordering = ('-modified_at',)

    search_fields = ('customer__name',)
    raw_id_fields = ['customer']
    actions = ['duplicate']

    def duplicate(modeladmin, request, queryset):
        """ Duplicate order with their dependencies. 
        for example: Clone Order A (containing Order_Details A1, A2) to a New Order B (containing new order_details B1,B2)    
        """""

        for order in queryset:
            order_details = order.details.all()
            order.id = None
            order.name = order.name + " (duplicated %s)" % get_random_string(2)
            order.save()
            for detail in order_details:
                detail.id = None
                detail.order = order
                detail.save()

    duplicate.short_description = "Duplicate selected orders with their dependencies"


class PaypalBillingPlanAdmin(admin.ModelAdmin):
    list_display = (
        'product_catalog', 'paypal_id'
    )


class PaypalTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'profile_id_link', 'txn_id', 'payment_time', 'created_at'
    )

    search_fields = ('order__customer__name', 'profile_id', 'txn_id')
    ordering = ('-payment_time',)
    raw_id_fields = ['order']

    def profile_id_link(self, tx):
        """
        :type tx: PaypalTransaction
        """
        return '{} <a href="{}" target="_blank">{}</a>'.format(
            tx.profile_id,
            get_paypal_url(tx.profile_id),
            get_paypal_favicon()
        )

    profile_id_link.allow_tags = True
    profile_id_link.short_description = "Paypal profile"


class BraintreeCustomerAdmin(admin.ModelAdmin):
    list_display = (
        'bt_id', 'user'
    )

    search_fields = ('user__email', 'user__name')
    raw_id_fields = ['user']


class BraintreeSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'bt_id', 'link_to_subscription', 'status', 'cancelled', 'created_at'
    )

    search_fields = ('subscription__name', 'bt_id')

    def link_to_subscription(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:core_subscription_change',
                    args=[obj.subscription.id]), obj.subscription.name)

    link_to_subscription.allow_tags = True
    link_to_subscription.short_description = "Subscription"


class BraintreePaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        'customer_id',
        'link_to_user',
        'link_to_customer',
        'token',
        'created_date',
        'succeed',
        'default',
        'type',
        'last_4_digits',
        'card_type',
        'expiration_date',
        'email_address',
    )

    search_fields = ('token', 'customer_id')

    ordering = ('-modified_at',)

    def created_date(self, obj):
        return obj.created_at.strftime(time_format)

    created_date.allow_tags = True
    created_date.short_description = 'Create date'
    created_date.admin_order_field = 'created_at'

    def link_to_user(self, obj):
        user = User.objects.get(auth_user__username=obj.customer_id[3:])
        return '<a href="{}">{}</a>'.format(
            reverse('admin:core_user_change',
                    args=[user.id]), user.email)

    def link_to_customer(self, obj):
        user = User.objects.get(auth_user__username=obj.customer_id[3:])
        customer = user.customer
        return '<a href="{}">{}</a>'.format(
            reverse('admin:core_customer_change',
                    args=[customer.id]), customer.name)

    link_to_user.allow_tags = True
    link_to_user.short_description = "User"

    link_to_customer.allow_tags = True
    link_to_customer.short_description = "Customer"


class BraintreeTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'completed_date', 'link_to_bt')

    search_fields = ('order__customer__name', 'bt_id')

    ordering = ('-modified_at',)

    raw_id_fields = ['order']

    def link_to_bt(self, obj):
        """
        :type obj: BraintreeTransaction
        """
        return '{} <a href="{}" target="_blank">{}</a>'.format(
            obj.bt_id,
            get_braintree_url("transactions", obj.bt_id),
            get_braintree_favicon()
        )

    link_to_bt.allow_tags = True
    link_to_bt.short_description = "Braintree id"


class FailedTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'link_to_potential', 'failed_date')

    @staticmethod
    def _link_to_crm(module, record_id):
        return ("<a target=\"_blank\" " +
                "href=\"https://crm.zoho.com/crm/EntityInfo.do?module={module}&id={record_id}\">{record_id}</a>"
                ).format(module=module, record_id=record_id)

    def link_to_potential(self, obj):
        if obj.potential_id:
            return self._link_to_crm(
                "Potentials", obj.potential_id
            )
        return ''

    link_to_potential.allow_tags = True
    link_to_potential.short_description = "Potential"

    def failed_date(self, obj):
        return obj.date.strftime(time_format)

    failed_date.allow_tags = True
    failed_date.short_description = 'Date'
    failed_date.admin_order_field = 'date'

    raw_id_fields = ['order']


class ZohoRecordAdmin(admin.ModelAdmin):
    list_display = ('customer', 'link_to_lead', 'link_to_account', 'link_to_potential')

    search_fields = ('customer__name',)

    @staticmethod
    def _link_to_crm(module, record_id):
        return ("<a target=\"_blank\" " +
                "href=\"https://crm.zoho.com/crm/EntityInfo.do?module={module}&id={record_id}\">{record_id}</a>"
                ).format(module=module, record_id=record_id)

    def link_to_potential(self, obj):
        if obj.potential_id:
            return self._link_to_crm(
                "Potentials", obj.potential_id
            )
        return ''

    link_to_potential.allow_tags = True
    link_to_potential.short_description = "Potential"

    def link_to_account(self, obj):
        if obj.account_id:
            return self._link_to_crm(
                "Accounts", obj.account_id
            )
        return ''

    link_to_account.allow_tags = True
    link_to_account.short_description = "Account"

    def link_to_lead(self, obj):
        if obj.lead_id:
            return self._link_to_crm(
                "Leads", obj.lead_id
            )
        return ''

    link_to_lead.allow_tags = True
    link_to_lead.short_description = "Lead"

    raw_id_fields = ['customer']


class PolicyAdmin(admin.ModelAdmin):
    list_display = ('product_category', 'per_user', 'customer_type',
                    'customer_region', 'offline_customer', 'customer_country',
                    'order_type', 'product', 'currency', 'catalog', 'vendor_console',
                    'minimal_quantity', 'tax_id')


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'continent', 'currency', 'translation')
    search_fields = ['name', 'currency']


class ProductCatalogAdmin(admin.ModelAdmin):
    list_display = ('product', 'catalog', 'price', 'per_user', 'self_service')


class VendorFieldAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'vendor_name', 'sm_name')


class VendorValueAdmin(admin.ModelAdmin):
    list_display = ('field', 'vendor_value', 'sm_value')


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'parent_category')

    class Meta:
        verbose_name = 'Product category'
        verbose_name_plural = 'product categories'


class GoogleTransferTokenAdmin(admin.ModelAdmin):
    list_display = ('customer', )
    search_fields = ['customer']


class ProductVersionAdmin(admin.ModelAdmin):
    pass


class ProductPlanAdmin(admin.ModelAdmin):
    pass


class DisplayProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'enabled',
        'highlighted',
        'showcase_alternate',
        'show_small',
    )
    list_editable = (
        'enabled',
        'highlighted',
        'showcase_alternate',
        'show_small',
    )

    def name(self, instance):
        return instance.displayed_product.name

    def get_queryset(self, request):
        qs = super(DisplayProductAdmin, self).get_queryset(request)
        current_product = request.session.get('display_product__current_product')
        action_type = request.session.get('display_product__action_type')
        if current_product:
            qs = qs.filter(current_product=current_product)
        if action_type:
            qs = qs.filter(type=action_type)
        return qs

    def get_urls(self):
        urls = super(DisplayProductAdmin, self).get_urls()
        custom_urls = [
            url(r'^edit_options/(?P<product_id>\d+)/(?P<action_type>.+)/$',
                self.edit_options,
                name='edit_product_display_options'),
            url(r'^select_products/$',
                self.select_products,
                name='select_products_to_copy_options'),
            url(r'^copy_options/$',
                self.copy_options,
                name='copy_product_display_options'),
        ]
        return custom_urls + urls

    def edit_options(self, request, product_id, action_type):
        product = get_object_or_404(Product, id=product_id)
        create_display_products_from_product(product)
        request.session['display_product__current_product'] = product.id
        request.session['display_product__action_type'] = action_type
        return redirect('admin:core_displayproduct_changelist')

    def select_products(self, request):
        form = SelectProducts()
        return render_to_response(
            'admin/select_products_to_copy_options.html',
            context={
                'form': form,
                'csrf_token': get_token(request),
            },
        )

    @csrf_protect_m
    def copy_options(self, request):
        form = SelectProducts(request.POST)
        if not form.is_valid():
            return redirect('admin:select_products_to_copy_options')

        for target_product in form.cleaned_data['products']:
            source_options = DisplayProduct.objects.filter(
                current_product=request.session['display_product__current_product']
            )
            create_display_products_from_product(target_product)
            target_options = DisplayProduct.objects.filter(
                current_product=target_product.id,
                displayed_product__in=source_options.values_list('displayed_product', flat=True)
            ).order_by('displayed_product')
            source_options = source_options.filter(
                displayed_product__in=target_options.values_list('displayed_product', flat=True)
            ).order_by('displayed_product')
            for source_option, target_option in map(None, source_options, target_options):
                target_option.enabled = source_option.enabled
                target_option.highlighted = source_option.highlighted
                target_option.showcase_alternate = source_option.showcase_alternate
                target_option.show_small = source_option.show_small
                target_option.save()

        return redirect('admin:core_displayproduct_changelist')


class DefaultProductPlanAdmin(admin.ModelAdmin):
    pass


class FeatureVersionAdmin(admin.ModelAdmin):
    pass


class FeatureProductCategoryAdmin(admin.ModelAdmin):
    pass


class ProductFeatureAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Catalog, CatalogAdmin)
admin.site.register(DiscountCode, DiscountCodeAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
# admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Order, OrderAdmin)
# admin.site.register(PaypalBillingPlan, PaypalBillingPlanAdmin)
admin.site.register(PaypalTransaction, PaypalTransactionAdmin)
# admin.site.register(BraintreeSubscription, BraintreeSubscriptionAdmin)
admin.site.register(BraintreeCustomer, BraintreeCustomerAdmin)
admin.site.register(SubscriptionProxy, SubscriptionProxyAdmin)
admin.site.register(BraintreeTransaction, BraintreeTransactionAdmin)
admin.site.register(BraintreePaymentMethod, BraintreePaymentMethodAdmin)
admin.site.register(ZohoCustomerRecord, ZohoRecordAdmin)
admin.site.register(FailedTransaction, FailedTransactionAdmin)
# admin.site.register(Policy, PolicyAdmin)
admin.site.register(ProductCatalog, ProductCatalogAdmin)
admin.site.register(VendorField, VendorFieldAdmin)
admin.site.register(VendorValue, VendorValueAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Vendor, admin.ModelAdmin)
admin.site.register(GoogleTransferToken, GoogleTransferTokenAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(ProductVersion, ProductVersionAdmin)
admin.site.register(ProductPlan, ProductPlanAdmin)
admin.site.register(DisplayProduct, DisplayProductAdmin)
admin.site.register(DefaultProductPlan, DefaultProductPlanAdmin)
admin.site.register(FeatureVersion, FeatureVersionAdmin)
admin.site.register(FeatureProductCategory, FeatureProductCategoryAdmin)
admin.site.register(ProductFeature, ProductFeatureAdmin)
