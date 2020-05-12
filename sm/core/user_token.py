import json

from django.utils import timezone


def get_key_name(key):
    return "sm:user_token:" + key


class UserTokenFactory(object):
    cache = None

    def get_cache(self):
        """

        :rtype : redis_cache.RedisCache
        """
        from django.core.cache import caches
        if self.cache is None:
            self.cache = caches['default']
        return self.cache

    def create(self, email, customer):
        """

        :rtype : UserToken
        """
        import time
        from uuid import uuid4
        c = UserToken()
        c.email = unicode(email)
        c.customer = unicode(customer)
        key = uuid4().hex
        self.get_cache().set(
            key=get_key_name(key),
            value=json.dumps({
                'email': email,
                'customer': customer
            }),
            timeout=c.expired_in
        )
        c.key = key
        c.created_at = timezone.now()
        return c

    def remove(self, key):
        self.get_cache().delete(get_key_name(key))

    def get(self, key):
        """
        :rtype: UserToken
        """
        value = self.get_cache().get(get_key_name(key))
        if value:
            value = json.loads(value)
            token = UserToken()
            token.customer = value['customer']
            token.key = key
            token.email = value['email']
            return token
        return None


user_token_factory = UserTokenFactory()


class UserToken(object):
    email = None
    customer = None
    key = None
    expired_in = 600
    created_at = None
