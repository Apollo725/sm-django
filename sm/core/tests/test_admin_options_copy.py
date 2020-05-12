from django.conf import settings
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from sm.core.models import (DisplayProduct, Product, ProductCategory,
                            ProductPlan, ProductType, ProductVersion,
                            ProductVersionEnum, SubscriptionPlan, User)
from sm.core.utils.model_utils import create_display_products_from_product


class AdminOptionsCopyTest(TestCase):
    '''
    Testing of product options creation and their copying from one products to
    others.
    '''

    CURRENT_PRODUCT_KEY = 'display_product__current_product'

    @classmethod
    def setUpClass(self):
        super(AdminOptionsCopyTest, self).setUpClass()
        product_category_a = ProductCategory.objects.create(
            name='Product category A',
            code='product_category_a',
        )
        product_category_b = ProductCategory.objects.create(
            name='Product category B',
            code='product_category_b',
        )

        product_version_pro = ProductVersion.objects.get(
            codename=ProductVersionEnum.PRO
        )

        annual_monthly_product_plan = ProductPlan.objects.get(
            codename=SubscriptionPlan.ANNUAL_MONTHLY,
        )

        Product.objects.create(
            name='Product 1A',
            code='product1a',
            category=product_category_a,
            vendor_sku='some_vendor_sku',
            version=product_version_pro,
            plan=annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        Product.objects.create(
            name='Product 2A',
            code='product2a',
            category=product_category_a,
            vendor_sku='some_vendor_sku',
            version=product_version_pro,
            plan=annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        Product.objects.create(
            name='Product 3A',
            code='product3a',
            category=product_category_a,
            vendor_sku='some_vendor_sku',
            version=product_version_pro,
            plan=annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        Product.objects.create(
            name='Product 1B',
            code='product1b',
            category=product_category_b,
            vendor_sku='some_vendor_sku',
            version=product_version_pro,
            plan=annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        Product.objects.create(
            name='Product 2B',
            code='product2b',
            category=product_category_b,
            vendor_sku='some_vendor_sku',
            version=product_version_pro,
            plan=annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )

        self.client = Client()
        credentials = {
            'username': settings.SM_ROOT_NAME,
            'password': settings.SM_ROOT_PASSWORD
        }
        self.client.login(**credentials)

        self.product1a = Product.objects.get(code='product1a')

    def test_option_creation_for_present_product(self):
        url = reverse(
            'admin:edit_product_display_options',
            kwargs={'product_id': self.product1a.id}
        )
        response = self.client.get(url)

        self.assertEquals(response.status_code, 302)
        self.assertEquals(
            self.CURRENT_PRODUCT_KEY in self.client.session,
            True
        )
        current_product = self.client.session[self.CURRENT_PRODUCT_KEY]
        self.assertEquals(current_product, self.product1a.id)

        displayed_product_ids = list(
            DisplayProduct.objects
            .filter(current_product=self.product1a.id)
            .values_list('displayed_product', flat=True)
        )
        category_products_ids = list(
            self.product1a.category.products.all()
            .values_list('id', flat=True)
        )
        category_products_ids.sort()
        displayed_product_ids.sort()
        self.assertSequenceEqual(
            displayed_product_ids,
            category_products_ids
        )

    def test_option_creation_for_absent_product(self):
        url = reverse(
            'admin:edit_product_display_options',
            kwargs={'product_id': 0}
        )
        response = self.client.get(url)

        self.assertEquals(response.status_code, 404)

    def test_options_copy(self):
        url = reverse('admin:copy_product_display_options')
        session = self.client.session
        session[self.CURRENT_PRODUCT_KEY] = self.product1a.id
        session.save()
        product2a = Product.objects.get(code='product2a')
        product3a = Product.objects.get(code='product3a')
        product2b = Product.objects.get(code='product2b')

        create_display_products_from_product(self.product1a)
        DisplayProduct.objects \
            .filter(
                current_product=self.product1a,
                displayed_product=product2a
            ) \
            .update(
                enabled=True,
                highlighted=True
            )
        data = {
            'products': [product3a.id, product2b.id]
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        options = DisplayProduct.objects.get(
            current_product=product3a,
            displayed_product=product2a
        )
        self.assertSequenceEqual(
            [options.enabled, options.highlighted, options.showcase_alternate, options.show_small],
            [True, True, False, False]
        )
        options = DisplayProduct.objects.get(
            current_product=product3a,
            displayed_product=self.product1a
        )
        self.assertSequenceEqual(
            [options.enabled, options.highlighted, options.showcase_alternate, options.show_small],
            [False, False, False, False]
        )
        options = DisplayProduct.objects.filter(
            current_product=product2b,
            displayed_product=product2a
        )
        self.assertFalse(options)
