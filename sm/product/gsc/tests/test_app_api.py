from __future__ import absolute_import

from unittest import skip

from django.test import TestCase

from sm.product.gsc.app_api import *
from sm.product.gsc.mocks import *
from django.utils import timezone

class Case(TestCase):
    @skip
    def test_update_subscription(self):
        with self.settings(
                GSC_PRODUCT_URL='http://127.0.0.1:8080'):
            add_default_catalog()

            customer = Customer.objects.create(
                name='alti.mobi'
            )

            catalog = get_default_catalog()

            sub = Subscription.objects.create(
                customer=customer,
                domain=customer.name,
                vendor_status=VendorStatus.PAID,
                vendor_licenses=20,
                expiry_date=timezone.now(),
                billable_licenses=20,
                catalog=catalog,
                product=catalog.get_tier(20).product,
                name="subscription of alti.mobi"
            )

            update_license(sub)

    @skip
    def test_get_plans(self):
        import braintree
        for plan in braintree.Plan.all():
            logger.info("Plan id: %s", plan.id)
