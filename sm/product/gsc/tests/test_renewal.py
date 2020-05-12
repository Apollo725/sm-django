from __future__ import absolute_import

import logging
from unittest import skip

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

from sm.product.gsc import cron
from sm.product.gsc import models
from sm.product.gsc import mocks


logger = logging.getLogger(__name__)


class Case(TestCase):
    def setUp(self):
        mocks.add_default_catalog()
        sub = self.create_subscription('a.com')  # expire date is before today
        sub.save()

        sub = self.create_subscription('b.com')  # paid expired version
        sub.vendor_status = models.VendorStatus.PAID
        sub.save()

        sub = self.create_subscription('c.com')  # renewal version
        sub.renewal_option = models.RenewalOption.RENEW
        sub.vendor_status = models.VendorStatus.PAID
        sub.save()

        sub = self.create_subscription('d.com')
        sub.trusted = True
        sub.save()

    def get_subscription(self, name):
        return models.Subscription.objects.get(name='GSC for {}'.format(name))

    def create_subscription(self, name):
        customer = models.Customer.objects.create(name=name)
        models.User.objects.create(customer=customer, email='user@' + name)

        return models.Subscription.objects.create(
            customer=customer,
            name='GSC for {}'.format(customer),
            product=models.get_default_catalog().get_tier(
                number=5, version=models.ProductVersionEnum.ENTERPRISE,
                plan=models.SubscriptionPlan.ANNUAL_YEARLY).product,
            catalog=models.get_default_catalog(),
            expiry_date=timezone.now() + relativedelta(days=-1),
            next_invoice_date=timezone.now() + relativedelta(days=-16),
            billable_licenses=0,
            vendor_licenses=0
        )

    def test_renew(self):
        cron_job = cron.RenewCustomers()
        cron_job.do()

        self.assertEquals(self.get_subscription('a.com').vendor_status, models.VendorStatus.EXPIRED_EVAL)
        self.assertEquals(self.get_subscription('b.com').vendor_status, models.VendorStatus.EXPIRED_PAID)
        self.assertEquals(self.get_subscription('c.com').vendor_status, models.VendorStatus.EXPIRED_PAID)
        # TODO(greg_eremeev) MEDIUM: should expiry_date.year equal `timezone.now().year + 1` or `timezone.now().year`?
        # self.assertEquals(self.get_subscription('c.com').expiry_date.year, timezone.now().year + 1)
        self.assertEquals(self.get_subscription('d.com').vendor_status, models.VendorStatus.EVAL)
