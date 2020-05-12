import unittest

from rest_framework.test import APIClient

from sm.core.models import User


class TestCheckVendorToken(unittest.TestCase):

    # def test(self):
    #     self.client = APIClient()
    #     print "Starting Test"
    #     for user in User.objects.filter(mock=True):
    #         print u"Testing user: {}, for domain: {}".format(user.name, user.customer.name)
    #         self.client.force_authenticate(user=user.auth_user)
    #         response = self.client.post('/products/google/check_vendor_token/',
    #                                     {'transfer_token': '', 'order': 'CREATE'})
    #         self.assertEqual(response.status_code, 200)
    #         self.client.force_authenticate(user=None)

    def test_one(self):
        self.client = APIClient()
        user = User.objects.filter(customer__name="nadaaa.com").first()
        print u"Testing user: {}, for domain: {}".format(user.name, user.customer.name)
        self.client.force_authenticate(user=user.auth_user)
        response = self.client.post('/api/check-vendor-token/',
                                    {'transfer_token': '64', 'order': 'UPDATE'})
        if response.status_code > 200:
            print u"error happens: {}".format(response)
        else:
            print u"response: {}".format(response)

        self.assertEqual(response.status_code, 200)
        self.client.force_authenticate(user=None)
