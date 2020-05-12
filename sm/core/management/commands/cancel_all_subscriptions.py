# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Synchronizing the payment method from braintree to sm"

    def handle(self, *modules, **options):
        from sm.core.braintree_helper import cancel_all_subscriptions
        cancel_all_subscriptions()
