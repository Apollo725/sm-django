from __future__ import absolute_import
from django.apps.config import AppConfig as DjAppConfig
from django.conf import settings
import logging

logger = logging.getLogger('mock_now')


class AppConfig(DjAppConfig):
    name = 'mock_now'

    def ready(self):
        # make a monkey-patch when DEBUG is true
        if settings.DEBUG:
            from mock_now import core
            core.monkey_patch()
            if 'mock_now.middlewares.MockNowMiddleware' not in settings.MIDDLEWARE_CLASSES:
                settings.MIDDLEWARE_CLASSES += (
                    'mock_now.middlewares.MockNowMiddleware', )
            logger.info("django.utils.timezone.now is patched")
