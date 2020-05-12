from __future__ import absolute_import

from django.test import TestCase

from sm.core.models import (Customer, Order, OrderDetail, ProductCatalog, User,
                            VendorProfile, VendorProfileClazz)
from sm.product.gsc import mocks
from sm.product.gsc.models import (PRODUCT_CLAZZ, PromotionCode,
                                   SubscriptionManager, get_default_catalog,
                                   get_gsc_product_category)

GSC_PRODUCT_CATEGORY = get_gsc_product_category()


class PromotionTest(TestCase):

    USER_EMAIL = "admin@foo.com"
    CUSTOMER_NAME = "foo.com"
    PASSWORD = 'notasecret'
    PR = 'B16BB0B6B1B0B'

    def setUp(self):
        mocks.add_default_catalog()
        self.customer = Customer.objects.create(name=self.CUSTOMER_NAME)
        self.user = User.objects.create(email=self.USER_EMAIL, customer=self.customer)

        catalog = get_default_catalog()
        PromotionCode.objects.create(id=1, code='BBBBBBB', catalog=catalog)
        profile = VendorProfile.objects.create(customer=self.customer, name=self.customer.name)
        VendorProfileClazz.objects.create(product_clazz=PRODUCT_CLAZZ, vendor_profile=profile)

    def test_promotion_code(self):
        subscription = SubscriptionManager(self.user.customer).ensure_exists()
        catalog = get_default_catalog()
        product = catalog.products.last()

        order = Order.objects.create(customer=self.user.customer, name='order', status='OPEN')
        OrderDetail.objects.create(
            order=order,
            product=product,
            catalog=catalog,
            sub_total=ProductCatalog.objects.get(product=product, catalog=catalog).price,
            subscription=subscription
        )
        subscription.order = order
        subscription.save()

        promotion = self.PR[:1] + self.PR[3:5] + self.PR[6:7] + self.PR[8:9] + self.PR[10:11] + self.PR[12:]
        date = self.PR[1:3] + self.PR[5:6] + self.PR[7:8] + self.PR[9:10] + self.PR[11:12]

        promotion_catalog = PromotionCode.objects.get(catalog__exact=catalog)
        self.assertEquals(promotion_catalog.code, promotion)

        subscription = SubscriptionManager(self.user.customer).ensure_exists()
        customer = self.user.customer

        order_detail = OrderDetail.objects.filter(
            order__customer=customer,
            product__category=GSC_PRODUCT_CATEGORY,
            subscription=SubscriptionManager(customer).get_subscription(),
            order__status='OPEN'
        ).order_by('-order__date').first()

        order_detail.catalog = promotion_catalog.catalog
        order_detail.subscription.catalog = promotion_catalog.catalog
        tier = order_detail.catalog.get_tier(
            order_detail.amount,
            version=order_detail.product.version,
            plan=order_detail.product.plan)
        order_detail.subtotal = tier.price
        order_detail.save()
        order_detail.subscription.save()
