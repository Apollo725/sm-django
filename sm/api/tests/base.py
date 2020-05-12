from rest_framework.test import APITestCase


class BaseAPITestCase(APITestCase):

    BASE_API_URL = '/api/'


class AuthenticatedWithUser(object):

    def __init__(self, client, user):
        self.client = client
        self.user = user

    def __enter__(self):
        self.client.force_authenticate(user=self.user)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.force_authenticate(user=None)
