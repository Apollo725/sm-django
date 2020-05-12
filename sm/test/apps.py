__author__ = 'jakub'

from django.apps.config import AppConfig as DjAppConfig


class AppConfig(DjAppConfig):
    name = 'sm.test'

    # noinspection PyUnresolvedReferences
    def ready(self):
        return
