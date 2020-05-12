from django.test import TestCase

from sm.core.user_token import UserTokenFactory


class UserTokenTestCase(TestCase):

    EMAIL = "test@test.com"
    CUSTOMER = 'test.com'

    def test_user_token(self):
        factory = UserTokenFactory()
        token = factory.create(self.EMAIL, self.CUSTOMER)

        self.assertIsNotNone(token.key)
        self.assertEqual(self.EMAIL, token.email)
        self.assertEqual(self.EMAIL, factory.get(token.key).email)
