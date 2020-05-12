from __future__ import absolute_import
from rest_framework.test import APITestCase
from sm.product.gsc.mocks import create_fake_profile
from sm.core.factories import VendorProfileClazzFactory, OrderFactory
import logging


logger = logging.getLogger(__name__)


class TestOrderViews(APITestCase):
    """
    """
    sanja = 0

    def setUp(self):
        """Initialize mock data for test
        """
        order = OrderFactory()
        self.sanja = order.id
        customer = order.customer
        logger.info("HIHIHIHI" + customer.name)
        create_fake_profile(customer)
        self.client.force_authenticate(user=customer.users.first().auth_user)

    def test_get_orders_view(self):
        """Test list orders view.
        """
        response = self.client.get('/api/orders/')
        logger.info(response.content)
        self.assertEquals(200, response.status_code)

    # def test_get_order_view(self):
    #     """Test get order view.
    #     """
    #     response = self.client.get('/api/order/{}'.format(self.sanja))
    #     logger.info(response.content)
    #     self.assertEquals(200, response.status_code)

