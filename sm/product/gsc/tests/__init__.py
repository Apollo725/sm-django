from __future__ import absolute_import

from unittest import skip

from django.test import Client
from django.test import TestCase

from sm.product.gsc.models import *
from sm.product.gsc.subscription_listener import on_subscription_cancel, on_subscription_payment

USER_EMAIL = "admin@foo.com"
CUSTOMER_NAME = "foo.com"
PASSWORD = 'notasecret'

import logging

logger = logging.getLogger(__name__)


class RegistrationTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name=CUSTOMER_NAME
        )

        self.user = User.objects.create(
            email=USER_EMAIL,
            customer=self.customer
        )

        auth_user = AuthUser.objects.get(sm=self.user)
        auth_user.set_password(PASSWORD)
        auth_user.save()

        self.client = Client()
        self.client.login(username=auth_user.username, password=PASSWORD)

    def test_update(self):
        vendor_profile, _ = VendorProfile.objects.update_or_create(
            dict(users=200, org_name='FOO'),
            customer=self.customer, name=self.customer.name)

        VendorProfileClazz.objects.update_or_create(
            vendor_profile=vendor_profile,
            product_clazz=PRODUCT_CLAZZ
        )
        phone_number = '111111111'
        name = 'Admin'
        reseller = 'google.com'
        resp = self.client.post(
            "/products/gsc/register", {
                'phone_number': phone_number,
                'name': name,
                'contact_email': USER_EMAIL,
                'reseller': reseller
            }
        )

        user = User.objects.get(email=USER_EMAIL)
        vendor_profile.refresh_from_db()
        self.assertEqual(USER_EMAIL, user.contact_email)
        self.assertEqual(phone_number, user.phone_number)
        self.assertEqual(name, user.name)
        self.assertEqual(reseller, vendor_profile.reseller)
        self.customer.refresh_from_db()
        self.assertEqual('FOO', self.customer.verbose_name)


class PaymentTest(TestCase):
    def setUp(self):
        from sm.product.gsc import mocks
        mocks.add_default_catalog()
        self.customer = Customer.objects.create(
            name=CUSTOMER_NAME
        )

        self.user = User.objects.create(
            email=USER_EMAIL,
            customer=self.customer
        )

        profile = VendorProfile.objects.create(customer=self.customer, name=self.customer.name)
        VendorProfileClazz.objects.create(product_clazz=PRODUCT_CLAZZ, vendor_profile=profile)

    @skip
    def test_payment_success(self):
        from django.utils import timezone
        subscription = SubscriptionManager(self.user.customer).ensure_exists()
        catalog = get_default_catalog()
        product = catalog.products.last()
        order = Order.objects.create(customer=self.customer, name='order')
        OrderDetail.objects.create(
            order=order,
            product=product,
            catalog=catalog,
            sub_total=ProductCatalog.objects.get(product=product, catalog=catalog).price
        )
        subscription.order = order
        subscription.save()
        PaypalTransaction.objects.create(profile_id='profile_id', order=order, payment_time=timezone.now())
        on_subscription_payment(None, 'profile_id', 'txn_id', params=dict(
            next_payment_date='02:00:00 Jan 30, 2016 PST'
        ))

        subscription.refresh_from_db()

        self.assertEquals(subscription.renewal_option, RenewalOption.RENEW)
        self.assertTrue(subscription.next_invoice_date >
                        timezone.datetime(2016, 1, 29,
                                          tzinfo=pytz.timezone('America/Los_Angeles'))
                        )

        on_subscription_cancel(None, 'profile_id')
        subscription.refresh_from_db()
        self.assertEquals(subscription.renewal_option, RenewalOption.CANCEL)


class ABTestCase(TestCase):
    def testAbTest(self):
        from sm.product.gsc import mocks
        mocks.add_default_catalog()
        mocks.add_discount_catalogs()

        offset = Catalog.objects.first().pk

        for pk in [offset, offset + 1, offset + 2]:
            catalog = Catalog.objects.get(pk=pk)
            catalog.default = True
            catalog.save()

        for domain in ['a.com', 'b.com', 'c.com']:
            customer = Customer.objects.create(
                name=domain
            )

            vendor_profile = VendorProfile.objects.create(
                customer=customer,
                name=domain
            )

            VendorProfileClazz.objects.create(
                product_clazz=PRODUCT_CLAZZ,
                vendor_profile=vendor_profile
            )

            User.objects.create(
                email='u@' + domain,
                customer=customer
            )

        domain_a = Customer.objects.get(name='a.com')
        offset_domain = domain_a.pk

        sub_a = SubscriptionManager(Customer.objects.get(name='a.com')).ensure_exists()
        sub_b = SubscriptionManager(Customer.objects.get(name='b.com')).ensure_exists()
        sub_c = SubscriptionManager(Customer.objects.get(name='c.com')).ensure_exists()

        self.assertEquals((offset_domain - 1) % 3 + offset, sub_a.catalog.pk)
        self.assertEquals(offset_domain % 3 + offset, sub_b.catalog.pk)
        self.assertEquals((offset_domain + 1) % 3 + offset, sub_c.catalog.pk)
