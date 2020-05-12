from __future__ import absolute_import
from rest_framework.test import APITestCase
from sm.product.gsc.mocks import create_fake_profile
from sm.core.factories import VendorProfileClazzFactory
import logging


logger = logging.getLogger(__name__)


class TestProfileViews(APITestCase):
    """Describe subscriptions list api test.
    """
    def setUp(self):
        """Initialize mock data for test
        """
        customer = VendorProfileClazzFactory().vendor_profile.customer
        create_fake_profile(customer)
        self.client.force_authenticate(user=customer.users.first().auth_user)

    def test_get_profile_view(self):
        """Test get profile view.
        """
        response = self.client.get('/api/profile/')
        logger.info(response.content)
        self.assertEquals(200, response.status_code)

    def test_update_profile_view(self):
        """Test update profile view.
        """
        response = self.client.put('/api/profile/', {
            "billingDetails": {
                "country": "United States",
                "state": "Alabama",
                "city": "AAa",
                "zipCode": "AWEa",
                "address": "AEWa"
            },
            "billingContact": {
                "name": "admin test-1.com",
                "email": "admin@test-1.com",
                "phoneNumber": "1511"
            },
            "reseller": None
        }, format='json')
        self.assertEquals(200, response.status_code)
        logger.info(response.content)