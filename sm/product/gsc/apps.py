from __future__ import absolute_import
from django.apps.config import AppConfig as DjAppConfig
from django.conf import settings
from django.dispatch import receiver

import logging

logger = logging.getLogger(__name__)


class AppConfig(DjAppConfig):
    name = "sm.product.gsc"

    def ready(self):
        # make a monkey-patch when DEBUG is true
        if settings.DEBUG:
            from mock_now import signals
            from . import renewer

            @receiver(signals.post_now_mocked, weak=False)
            def renew_and_expire(*args, **kwargs):
                renewer.renew()
                renewer.expire_subscriptions()
                logger.info("GSC subscriptions are renewed")

            logger.info("Change server time will trigger renew functions")

        from sm.core.paypal.ipn import subscription_cancel
        from sm.core.paypal.ipn import subscription_payment
        from sm.core.paypal.ipn import subscription_failed
        from sm.product.gsc.subscription_listener import on_subscription_cancel
        from sm.product.gsc.subscription_listener import on_subscription_payment
        from sm.product.gsc.subscription_listener import on_subscription_failed

        subscription_cancel.connect(on_subscription_cancel)
        subscription_payment.connect(on_subscription_payment)
        subscription_failed.connect(on_subscription_failed)
