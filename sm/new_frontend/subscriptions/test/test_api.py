from __future__ import absolute_import
from rest_framework.test import APITestCase
from rest_framework.permissions import AllowAny
from sm.new_frontend.subscriptions.views import UpsertDetectedSubscriptionView
from sm.product.gsc.mocks import *
from sm.core.factories import *
from sm.core.models import *
from collections import namedtuple
import json
import logging
import django
django.setup()
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

logger = logging.getLogger(__name__)


class TestSubscriptionListAPI(APITestCase):
    """

    Describe subscriptions list api test.
    """

    def setUp(self):
        """

        Initialize mock data for test
        """

        customer = VendorProfileClazzFactory().vendor_profile.customer
        subscription = SubscriptionFactory(customer=customer)
        catalog = CatalogFactory(name='Boogle Product')
        category = ProductCategoryFactory(name='S Vault', code='SVault')
        product = ProductFactory(code='sanja_pro_flex_prepaid', name='Sanja professional version (flex prepaid)',
                                 category=category)

        SubscriptionFactory(catalog=catalog, customer=subscription.customer,
                            product=product, order__status=OrderStatus.CREATED, parent_subscription=subscription)
        self.client.force_authenticate(user=subscription.customer.users.first().auth_user)

    def test_get_invalid_subscriptions(self):
        """

        Test for invalid request for subscriptions api.
        """
        response = self.client.get('/api/subscriptions/', {'layout': 'table'})
        self.assertEquals(400, response.status_code)

    def test_get_subscription_by_list(self):
        """

        Test for subscriptions listed by list view
        """
        response = self.client.get('/api/subscriptions/', {'layout': 'list'})
        logger.info('resp: {}'.format(response.content))
        content = json.loads(response.content)
        self.assertEquals(content['count'], 2)

    def test_get_subscription_by_encapsulate(self):
        """

        Test for subscriptions listed by encapsulate view
        """
        response = self.client.get('/api/subscriptions/', {'layout': 'encapsulate'})
        logger.info('resp: {}'.format(response.content))
        content = json.loads(response.content)
        self.assertEquals(content['count'], 1)


@patch.object(UpsertDetectedSubscriptionView, 'permission_classes', new=[AllowAny])
class TestSubscriptionUpsertAPI(APITestCase):
    """

    Describe subscriptions upsert api test.
    """

    DATA_TUPLE = namedtuple('TestData', ('vendor_sku', 'domain', 'vendor_licenses'))
    TEST_DATA_NEW = (
        {'vendor_sku': 'Google-Drive-storage-50GB', 'domain': 'gappsexperts.com', 'vendor_licenses': 10},
        {'vendor_sku': 'Google-Apps-For-Business', 'domain': 'gappsexperts.com', 'vendor_licenses': 1},
        {'vendor_sku': 'Google-Vault', 'domain': 'gappsexperts.com', 'vendor_licenses': 2},
        {'vendor_sku': 'Google-Drive-storage-4TB', 'domain': 'gappsexperts.com', 'vendor_licenses': 20},
        {'vendor_sku': 'Google-Drive-storage-8TB', 'domain': 'gappsexperts.com', 'vendor_licenses': 5},
    )

    TEST_DATA_UPDATE = (
        {'vendor_sku': 'Google-Drive-storage-50GB', 'domain': 'gappsexperts.com', 'vendor_licenses': 6},
        {'vendor_sku': 'Google-Apps-Unlimited', 'domain': 'gappsexperts.com', 'vendor_licenses': 7},
        {'vendor_sku': 'Google-Vault', 'domain': 'gappsexperts.com', 'vendor_licenses': 5},
        {'vendor_sku': 'Google-Drive-storage-4TB', 'domain': 'gappsexperts.com', 'vendor_licenses': 13},
        {'vendor_sku': 'Google-Drive-storage-16TB', 'domain': 'gappsexperts.com', 'vendor_licenses': 16},
    )

    def validate_subscription(self, gsuite_cnt, gvault_cnt, gdrive_cnt, create=True):
        if create:
            response = self.client.put('/api/vendor/detected-subscriptions/', json.dumps(self.TEST_DATA_NEW),
                                       content_type="application/json")
            data = self.TEST_DATA_NEW
        else:
            response = self.client.put('/api/vendor/detected-subscriptions/', json.dumps(self.TEST_DATA_UPDATE),
                                       content_type="application/json")
            data = self.TEST_DATA_UPDATE
        logger.info(response)
        drive_category = None
        for test_data in data:
            customer = Customer.objects.filter(name=test_data['domain'])
            product = Product.objects.filter(vendor_sku=test_data['vendor_sku'], plan="").first()
            subscription = Subscription.objects.filter(customer=customer,
                                                       product__vendor_sku=test_data['vendor_sku']).first()
            self.assertEquals(200, response.status_code)
            self.assertEquals(subscription.status, SubscriptionStatus.DETECTED.value)
            self.assertEquals(subscription.domain, test_data['domain'])
            self.assertEquals(subscription.product, product)
            self.assertEquals(subscription.saw_price, False)
            self.assertEquals(subscription.vendor_licenses, subscription.vendor_users)
            self.assertEquals(subscription.vendor_users, test_data['vendor_licenses'])
            self.assertEquals(subscription.product.vendor_sku, test_data['vendor_sku'])
            self.assertEquals(subscription.unbound, True)

            if product.category is not None and product.category.code == 'GSUITE':
                subscription_count = Subscription.objects.filter(customer=customer,
                                                                 product__category=product.category).count()
                self.assertEquals(subscription_count, gsuite_cnt)
            if product.category is not None and product.category.code == 'GVAULT':
                subscription_count = Subscription.objects.filter(customer=customer,
                                                                 product__category=product.category).count()
                self.assertEquals(subscription_count, gvault_cnt)
            if product.category is not None and product.category.code == 'GDRIVE':
                drive_category = product.category

        subscription_count = Subscription.objects.filter(customer=customer,
                                                         product__category=drive_category).count()
        self.assertEquals(subscription_count, gdrive_cnt)

    def test_upsert_subscriptions(self):
        """

        Test for invalid request for subscriptions api.
        """

        # test for create new subscription
        self.validate_subscription(gsuite_cnt=1, gvault_cnt=1, gdrive_cnt=3, create=True)
        # test for update subscription
        self.validate_subscription(gsuite_cnt=1, gvault_cnt=1, gdrive_cnt=3, create=False)
