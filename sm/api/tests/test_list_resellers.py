import json

from django.test import TestCase
from rest_framework import status
from django.core.urlresolvers import reverse

from sm.core.models import Customer, CustomerType


class TestResllerAPI(TestCase):

    CUSTOMER_NAMES = 'customer.com', 'customer_1.com'
    CUSTOMER_TYPES = CustomerType.GAE_RESELLER, CustomerType.EX_RESELLER
    CUSTOMERS_DATA = zip(CUSTOMER_NAMES, CUSTOMER_TYPES)

    def test_retrieve_reseller(self):
        for customer_name, customer_type in self.CUSTOMERS_DATA:
            Customer.objects.create(name=customer_name, type=customer_type)

        url = reverse('api:reseller')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resellers = json.loads(response.content)

        self.assertEquals(1, len(resellers))
        self.assertEquals(resellers[0]['name'], self.CUSTOMERS_DATA[0][0])
