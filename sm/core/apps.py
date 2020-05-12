__author__ = 'hoozecn'

from django.apps.config import AppConfig as DjAppConfig


class AppConfig(DjAppConfig):
    name = 'sm.core'

    # noinspection PyUnresolvedReferences
    def ready(self):
        import sm.core.triggers
        import braintree
        from django.conf import settings

        if settings.BRAINTREE_SANDBOX:
            env = braintree.Environment.Sandbox
        else:
            env = braintree.Environment.Production

        braintree.Configuration.configure(
            env,
            merchant_id=settings.BRAINTREE_MERCHANT_ID,
            public_key=settings.BRAINTREE_PUBLIC_KEY,
            private_key=settings.BRAINTREE_PRIVATE_KEY)
