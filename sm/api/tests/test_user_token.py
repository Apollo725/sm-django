import json
import logging

from bunch import Bunch
from rest_framework import status
from django.core.urlresolvers import reverse

from sm.api.tests.base import BaseAPITestCase
from sm.core.models import Customer, User, AuthUser


logger = logging.getLogger(__name__)


class UserTokenTests(BaseAPITestCase):

    USER_EMAIL = 'test@test.com'

    def setUp(self):
        user = AuthUser.objects.create_superuser(username='test', email=None, password='test')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Token {}'.format(user.auth_token.key)

    def test_create_user_token(self):
        customer = Customer.objects.create(name='test.com')
        User.objects.create(customer=customer, email=self.USER_EMAIL)

        url = reverse('api:user-token-detail', kwargs={'email': self.USER_EMAIL, 'customer': customer})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.USER_EMAIL, Bunch(json.loads(response.content)).email)
