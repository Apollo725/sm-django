from django.test import TestCase

from sm.core.models import (Catalog, Order, OrderDetail, OrderDetailType,
                            OrderStatus, OrderType, Product, ProductPlan,
                            ProductVersion, ProductVersionEnum, Subscription,
                            SubscriptionPlan, VendorProfile)
from sm.product.google.utility.order_util import (create_order_instance,
                                                  create_order_detail_instance,
                                                  order_detail_policy_add,
                                                  order_detail_policy_new,
                                                  order_detail_policy_renew,
                                                  order_detail_policy_transfer,
                                                  order_detail_policy_upgrade,
                                                  order_detail_update,
                                                  order_update)
from sm.product.gsc.models import get_gsc_product_category


class OrderPolicyTestCase(TestCase):
    def setUp(self):
        self.subscription = Subscription.objects.filter(
            customer__isnull=False,
            product__productcatalog__catalog__isnull=False,
            product__tier_number__gte=1
        ).first()
        self.subscription_with_no_tier = Subscription.objects.filter(
            customer__isnull=False,
            product__productcatalog__catalog__isnull=False,
            product__tier_number=-1
        ).first()
        self.vendor_profile = VendorProfile.objects \
            .filter(customer=self.subscription.customer) \
            .first()
        self.product = Product.objects.get(
            category=get_gsc_product_category,
            tier_number__lt=0,
            plan=ProductPlan.objects.get(codename=SubscriptionPlan.ANNUAL_YEARLY),
            version=ProductVersion.objects.get(codename=ProductVersionEnum.PRO)
        )
        self.detail = OrderDetail.objects \
            .filter(
                subscription__isnull=False,
                order__status=OrderStatus.DRAFT,
                product__tier_number__lte=0
            ).first()
        self.detail_without_subscription, _ = OrderDetail.objects.get_or_create(
            order=Order.objects.order_by('id').first(),
            product=Product.objects.order_by('id').first(),
            catalog=Catalog.objects.order_by('id').first(),
            subscription=None,
            description='',
            unit_price=10,
            amount=100,
            sub_total=1000,
            discount=0.0,
            minimal_quantity=True,
            status=OrderStatus.DRAFT,
            type=OrderDetailType.ADD,
            tax=None,
            from_date=None,
            to_date=None,
            expiry=None,
            extension=None,
            refunded_amount=None,
            minimal_order=None,
        )

    def test_order_detail_policies(self):
        # For action 'NEW' can be passed or only product or subscription not
        # mandatory bouth.
        # Case for only subscription.
        result = order_detail_policy_new(
            vendor_profile=self.vendor_profile,
            detail=self.detail
        )
        self.assertIsNotNone(result['minimal_order'])
        self.assertIsNotNone(result['expiry'])
        self.assertIsNotNone(result['amount'])
        self.assertIsNotNone(result['from_date'])
        self.assertIsNotNone(result['to_date'])
        self.assertIsNone(result['extension'])
        self.assertIsNone(result['refunded_amount'])
        self.assertIsNotNone(result['unit_price'])
        # Case for only product.
        result = order_detail_policy_new(
            vendor_profile=self.vendor_profile,
            detail=self.detail_without_subscription
        )
        self.assertIsNotNone(result['minimal_order'])
        self.assertIsNotNone(result['expiry'])
        self.assertIsNotNone(result['amount'])
        self.assertIsNotNone(result['from_date'])
        self.assertIsNotNone(result['to_date'])
        self.assertIsNone(result['extension'])
        self.assertIsNone(result['refunded_amount'])
        self.assertIsNotNone(result['unit_price'])

        # For action 'ADD' required only subscription.
        result = order_detail_policy_add(
            vendor_profile=self.vendor_profile,
            detail=self.detail
        )
        self.assertIsNotNone(result['minimal_order'])
        self.assertIsNotNone(result['expiry'])
        self.assertIsNotNone(result['amount'])
        self.assertIsNotNone(result['from_date'])
        self.assertIsNotNone(result['to_date'])
        self.assertIsNotNone(result['extension'])
        self.assertIsNotNone(result['unit_price'])
        self.assertIsNone(result['refunded_amount'])

        # For action 'UPGRADE' required product and subscription.
        result = order_detail_policy_upgrade(
            vendor_profile=self.vendor_profile,
            detail=self.detail
        )
        self.assertIsNotNone(result['minimal_order'])
        self.assertIsNotNone(result['expiry'])
        self.assertIsNotNone(result['amount'])
        self.assertIsNotNone(result['from_date'])
        self.assertIsNotNone(result['to_date'])
        self.assertIsNotNone(result['extension'])
        self.assertIsNotNone(result['refunded_amount'])
        self.assertIsNotNone(result['unit_price'])

        # For action 'TRANSFER' we return everything None except amount. amount
        # returned as is.
        result = order_detail_policy_transfer(
            vendor_profile=self.vendor_profile,
            detail=self.detail
        )
        self.assertIsNone(result['minimal_order'])
        self.assertIsNone(result['expiry'])
        self.assertIsNotNone(result['amount'])
        self.assertIsNotNone(result['from_date'])
        self.assertIsNone(result['to_date'])
        self.assertIsNone(result['extension'])
        self.assertIsNone(result['refunded_amount'])
        self.assertIsNone(result['unit_price'])

        result = order_detail_policy_renew(
            vendor_profile=self.vendor_profile,
            detail=self.detail
        )
        self.assertIsNone(result['minimal_order'])
        self.assertIsNone(result['expiry'])
        self.assertIsNone(result['amount'])
        self.assertIsNone(result['from_date'])
        self.assertIsNone(result['to_date'])
        self.assertIsNone(result['extension'])
        self.assertIsNone(result['refunded_amount'])
        self.assertIsNone(result['unit_price'])

    def test_order_init(self):
        order = create_order_instance(
            customer=self.subscription.invoiced_customer,
            name='Test order name'
        )
        order.save()
        self.assertEqual(order.name, 'Test order name')
        self.assertEqual(order.status, OrderStatus.DRAFT)

        not_draft_order = Order.objects \
            .exclude(details__status=OrderStatus.DRAFT) \
            .first()

        self.assertRaises(
            ValueError,
            order_update,
            order=not_draft_order
        )

        draft_order = Order.objects \
            .filter(details__status=OrderStatus.DRAFT) \
            .first()

        detail = create_order_detail_instance(
            order=order,
            product=self.product,
            catalog=self.subscription.catalog
        )
        self.assertEqual(detail.status, OrderStatus.DRAFT)
        detail.type = OrderDetailType.NEW
        detail.save()

        order_detail_update(order_detail=order.details.first())
