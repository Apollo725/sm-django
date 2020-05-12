from datetime import timedelta

import factory
from django.utils import timezone

from sm.core.models import (AuthUser, Catalog, Customer, CustomerType, Order,
                            OrderDetail, OrderStatus, Product, ProductCatalog,
                            ProductCategory, ProductVersionEnum, RenewalOption,
                            Subscription, SubscriptionPaymentMethod,
                            SubscriptionPlan, SubscriptionStatus, User,
                            VendorProfile, VendorProfileClazz, VendorStatus,
                            ZohoCustomerRecord)


class AuthUserFactory(factory.DjangoModelFactory):

    class Meta:
        model = AuthUser


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User

    name = 'Sanja Test'
    email = 'Sanja@sanja.econsulting.fr'
    contact_email = 'Sanja@sanja.econsulting.fr'
    phone_number = '+78764346235'

    @factory.post_generation
    def auth_user(self, create, extracted, **kwargs):
        if create:
            self.auth_user = AuthUserFactory(username=self.name)
            self.save()


class ZohoCustomerRecordFactory(factory.DjangoModelFactory):

    class Meta:
        model = ZohoCustomerRecord

    lead_id = factory.Sequence(lambda _id: _id)
    account_id = factory.Sequence(lambda _id: _id)
    potential_id = factory.Sequence(lambda _id: _id)


class CustomerFactory(factory.DjangoModelFactory):

    class Meta:
        model = Customer

    name = 'sanja.econsulting.fr'
    org_name = 'sanja.econsulting.fr'
    type = CustomerType.PROSPECT.value
    balance = 100
    install_status = 'Registered+Granted'
    source = 'GSC Install - App'
    registered = True
    last_payment_date_raw = timezone.now()
    last_payment_outcome_raw = 'Braintree Success'
    last_payment_id_raw = 'braintree:mpbmqzb4'
    last_payment_type = 'new'

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        #if create:
            UserFactory(customer=self)

    @factory.post_generation
    def zoho_customer_record(self, create, extracted, **kwargs):
        if create:
            ZohoCustomerRecordFactory(customer=self)


class VendorProfileFactory(factory.DjangoModelFactory):

    class Meta:
        model = VendorProfile

    customer = factory.SubFactory(CustomerFactory)
    name = "jakub.econsulting.fr"


class VendorProfileClazzFactory(factory.DjangoModelFactory):

    class Meta:
        model = VendorProfileClazz

    vendor_profile = factory.SubFactory(VendorProfileFactory)
    product_clazz = "GSC"


class OrderDetailFactory(factory.DjangoModelFactory):

    class Meta:
        model = OrderDetail

    amount = 50
    sub_total = 20


class OrderFactory(factory.DjangoModelFactory):

    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    name = 'Gsc for jakub.econsulting.fr (new subscription)'
    conditions = 'conditions'
    terms = 'terms'
    due_date = timezone.now() + timedelta(days=1)
    currency = 'USD'
    discount = 0
    tax = 0
    status = OrderStatus.CREATED.value


class CatalogFactory(factory.DjangoModelFactory):

    class Meta:
        model = Catalog

    name = 'Boogle'


class ProductCategoryFactory(factory.DjangoModelFactory):

    class Meta:
        model = ProductCategory

    code = 'GSC'
    name = 'Shared Contacts for G Suite'


class ProductFactory(factory.DjangoModelFactory):

    class Meta:
        model = Product

    code = 's2_pro_flex_prepaid'
    name = 's2professional version (flex prepaid)'
    # purchase_price = 0
    # list_price = 0
    version = ProductVersionEnum.PRO.value
    plan = SubscriptionPlan.FLEX_PREPAID
    category = factory.SubFactory(ProductCategoryFactory)


class SubscriptionFactory(factory.DjangoModelFactory):

    class Meta:
        django_get_or_create = ['customer', 'product']
        model = Subscription

    name = 'GSC for jakub.econsulting.fr'
    customer = factory.SubFactory(CustomerFactory)
    product = factory.SubFactory(ProductFactory)
    catalog = factory.SubFactory(CatalogFactory)
    trial = False
    domain = 'jakub.econsulting.fr'
    payment_method = SubscriptionPaymentMethod.PAYPAL_AUTO.value
    trusted = False
    status = SubscriptionStatus.ACTIVE.value
    max_cap = None
    currency = 'USD'
    saw_price = True
    start_plan_date = None
    plan = SubscriptionPlan.ANNUAL_YEARLY.value
    renewal_option = RenewalOption.CANCEL.value
    expiry_date = timezone.now() + timedelta(days=5)
    billable_licenses = 2
    vendor_licenses = 5
    vendor_status = VendorStatus.EVAL.value
    vendor_plan = SubscriptionPlan.ANNUAL_YEARLY.value
    payment_gateway = 'Braintree GAE'
    parent_subscription = None

    @factory.post_generation
    def post_generation(self, create, extracted, **kwargs):
        if create:
            ProductCatalog.objects.get_or_create(product=self.product, catalog=self.catalog)

    @factory.post_generation
    def invoiced_customer(self, create, extracted, **kwargs):
        if create:
            self.invoiced_customer = self.customer
            self.save()

    @factory.post_generation
    def order(self, create, extracted, **kwargs):
        if create:
            self.order = OrderFactory(customer=self.customer, **kwargs)
            self.save()
            OrderDetailFactory(subscription=self, order=self.order, product=self.product, catalog=self.catalog)
