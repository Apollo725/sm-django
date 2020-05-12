import logging
from unittest import skip

import paypalrestsdk
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from sm.core.paypal.api import api


logger = logging.getLogger(__name__)


class TestPaypal(TestCase):

    @skip("skip to fetch event types")
    def test_list_webhooks(self):
        event_types = paypalrestsdk.WebhookEventType.all(api=api)
        logger.info("Event types %s", event_types)

    @skip("skip to fetch transactions")
    def test_get_transaction(self):
        date_format = '%Y-%m-%d'
        transactions = paypalrestsdk.BillingAgreement(dict(
            id='I-6PK9NDKY8HBW'
        ), api=api).search_transactions(
            start_date=(timezone.now() + relativedelta(days=-1)).strftime(date_format),
            end_date=(timezone.now() + relativedelta(days=1)).strftime(date_format),
            api=api
        )
        if not transactions.success():
            raise Exception(transactions.error)
        logger.info("Transactions: %s", transactions)
