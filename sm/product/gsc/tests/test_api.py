from __future__ import absolute_import

import logging

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from sm.product.gsc.mocks import add_default_catalog
from sm.product.gsc.models import (AuthUser, PaypalTransaction, Subscription, User, Customer, SubscriptionManager,
                                   VendorStatus)


logger = logging.getLogger(__name__)


class SubscriptionTests(APITestCase):

    CUSTOMER_NAME = 'foo.com'

    def setUp(self):
        # TODO(greg_eremeev) MEDIUM: need to make request from plain user
        user = AuthUser.objects.create_superuser(username='test', email=None, password='test')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Token {}'.format(user.auth_token.key)

    def test_get_subscription(self):
        response = self.client.get(reverse('api:gsc:subscription-detail', kwargs={'customer': self.CUSTOMER_NAME}))
        self.assertEquals(404, response.status_code)
        self.assertTrue("detail" in response.content and "Not found" in response.content)

    def test_update_subscription(self):
        self.test_create_vendor_profile()

        url = reverse('api:gsc:subscription-detail', kwargs={'customer': self.CUSTOMER_NAME})
        response = self.client.get(url)

        self.assertEqual(response.data['domain'], self.CUSTOMER_NAME)
        logger.info("subscription-detail: %s", response.data)

        self.client.put(url, data=dict(renewal_option='RENEW'))
        response = self.client.get(url)

        self.assertEqual(response.data['renewal_option'], 'RENEW')

        request_data = {'vendor_licenses': 100, 'catalog_id': 2, 'txn_id': 'txn_id', 'profile_id': 'profile_id'}
        self.client.put(url, data=request_data)

        txn = PaypalTransaction.objects.first()
        sub = Subscription.objects.first()
        self.assertEqual(txn.profile_id, 'profile_id')
        self.assertEqual(txn.txn_id, 'txn_id')
        self.assertEqual(sub.order, txn.order)

    def test_create_account(self):
        email_address = "admin@foo.com"
        response = self.client.put(reverse(
            'api:gsc:user-detail', kwargs={'email': email_address, 'customer': self.CUSTOMER_NAME}))

        logger.info("resp: %s", response.content)
        self.assertEquals(201, response.status_code)

        response = self.client.put(reverse(
            'api:gsc:user-detail', kwargs={'email': email_address, 'customer': self.CUSTOMER_NAME}))

        logger.info("resp: %s", response.content)
        self.assertEquals(200, response.status_code)

        self.assertEquals(1, User.objects.filter(email=email_address).count())
        self.assertEquals(1, Customer.objects.filter(name=self.CUSTOMER_NAME).count())

    def test_create_profile(self):
        address = 'Hangzhou'
        Customer.objects.create(name=self.CUSTOMER_NAME)

        url = reverse('api:gsc:profile-detail', kwargs={'customer': self.CUSTOMER_NAME})
        response = self.client.get(url)

        logger.info('resp: {}'.format(response.content))
        self.assertEquals(404, response.status_code)

        response = self.client.put(url, {'city': address})
        logger.info('resp: {}'.format(response.content))
        self.assertEquals(201, response.status_code)

        response = self.client.get(url)
        logger.info('resp: {}'.format(response.content))
        self.assertEquals(200, response.status_code)
        self.assertEquals(address, response.data['city'])

    def test_create_vendor_profile(self):
        user_number = 200
        customer = Customer.objects.create(name=self.CUSTOMER_NAME)
        add_default_catalog()

        url = reverse('api:gsc:vendor-profile-detail', kwargs={'customer': self.CUSTOMER_NAME})
        response = self.client.get(url)
        self.assertEquals(404, response.status_code)

        response = self.client.put(url, {'users': user_number})
        self.assertEquals(201, response.status_code)

        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        self.assertEquals(user_number, response.data['users'])

        subscription = SubscriptionManager(customer).get_subscription()
        self.assertIsNotNone(subscription)

        self.assertEquals(VendorStatus.EVAL, subscription.vendor_status)
        self.assertEquals(0, subscription.vendor_licenses)
        self.assertEquals(200, subscription.billable_licenses)
