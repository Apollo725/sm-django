from django.test import TestCase
from django.utils import timezone
import django

from sm.core.models import Subscription, VendorProfile, SubscriptionStatus
from sm.core.factories import Product
from collections import namedtuple


class VendorProfileTest(TestCase):
    DATA_TUPLE = namedtuple('TestData', ('apps_version', 'max_licenses', 'apps_creation', 'users', 'product_code'))
    TEST_DATA = (
        DATA_TUPLE('standard', 5, timezone.now(), 10,'GSUITE_STANDARD_NO_PLAN'),
        # DATA_TUPLE('education', 15, timezone.now(), 15, 'GSUITE_EDU_NO_PLAN'),
        # DATA_TUPLE('premier', 25, timezone.now(), 20, 'GSUITE_PREMIER_NO_PLAN'),
        # DATA_TUPLE('free', 35, timezone.now(), 25, 'GSUITE_FREE_NO_PLAN'),
    )

    @staticmethod
    def _update_vendor_profile(vendor_profile, data_tuple):
        vendor_profile.apps_version = data_tuple.apps_version
        vendor_profile.max_licenses = data_tuple.max_licenses
        vendor_profile.apps_creation = data_tuple.apps_creation
        vendor_profile.users = data_tuple.users
        vendor_profile.save()

    def test_update_subscription(self):
        django.setup()

        from sm.core.factories import VendorProfileFactory

        for index, data_tuple in enumerate(self.TEST_DATA):
            product, _ = Product.objects.get_or_create(code=data_tuple.product_code)

            if index == 0:
                vendor_profile = VendorProfileFactory(
                    apps_version=self.TEST_DATA[0].apps_version,
                    max_licenses=self.TEST_DATA[0].max_licenses,
                    apps_creation=self.TEST_DATA[0].apps_creation,
                    users=self.TEST_DATA[0].users)
            else:
                vendor_profile = VendorProfile.objects.first()
            old_subscription = Subscription.objects.filter(customer=vendor_profile.customer, product=product).exists()

            if index != 0:
                self._update_vendor_profile(vendor_profile, data_tuple)
            subscription = Subscription.objects.filter(customer=vendor_profile.customer, product=product).first()

            self.assertEquals(subscription.vendor_licenses, data_tuple.users)
            self.assertEquals(subscription.vendor_users, data_tuple.users)
            self.assertEquals(subscription.max_cap, data_tuple.max_licenses)

            if not old_subscription:
                self.assertEquals(subscription.status, SubscriptionStatus.DRAFT.value)
                self.assertEquals(subscription.domain, vendor_profile.name)
                self.assertEquals(subscription.saw_price, False)
                self.assertEquals(subscription.unbound, True)
