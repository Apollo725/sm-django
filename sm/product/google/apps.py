from __future__ import absolute_import
from django.apps.config import AppConfig


class GoogleAppConfig(AppConfig):
    name = "sm.product.google"

    def ready(self):
        return
