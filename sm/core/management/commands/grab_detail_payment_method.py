# -*- coding: utf-8 -*-
from braintree.exceptions.braintree_error import BraintreeError
from django.core.management.base import BaseCommand, CommandError
from sm.core.braintree_helper import get_payment_detail, save_payment_detail
from sm.core import models
import logging

from sm.core.paypal.billing_plan import dump_errors
from sm.product.gsc.models import disable_payment_method

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fill information about payments from braintree by token"

    def handle(self, *modules, **options):
        bpm_all = models.BraintreePaymentMethod.objects.filter(type__isnull=True)

        for bpm in bpm_all:
            try:
                payment = get_payment_detail(bpm.token)
                save_payment_detail(payment)
            except BraintreeError as e:
                logger.warn("Can't find token %s:%s, error: %s", bpm.customer_id, bpm.token, dump_errors(e))
                disable_payment_method(bpm.token)
