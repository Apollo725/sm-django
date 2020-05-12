import json
from datetime import datetime

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from sm.core.factories import SubscriptionFactory
from sm.core.models import (Catalog, Customer, FeatureProductCategory,
                            FeatureVersion, Product, ProductCatalog,
                            ProductCategory, ProductFeature, ProductPlan,
                            ProductType, ProductVersion, ProductVersionEnum,
                            Subscription, SubscriptionPlan)
from sm.core.utils.model_utils import create_display_products_from_product


class TestPricingAPI(APITestCase):
    def setUp(self):
        self.product_category_a, _ = ProductCategory.objects.get_or_create(
            name='Product category A',
            code='product_category_a',
        )

        self.product_version_pro = ProductVersion.objects.get(
            codename=ProductVersionEnum.PRO
        )
        self.product_version_basic = ProductVersion.objects.get(
            codename=ProductVersionEnum.BASIC
        )

        self.annual_monthly_product_plan = ProductPlan.objects.get(
            codename=SubscriptionPlan.ANNUAL_MONTHLY
        )
        self.annual_yearly_product_plan = ProductPlan.objects.get(
            codename=SubscriptionPlan.ANNUAL_YEARLY
        )

        self.product1a, _ = Product.objects.get_or_create(
            name='Product 1A',
            code='product1a',
            category=self.product_category_a,
            vendor_sku='some_vendor_sku',
            version=self.product_version_pro,
            plan=self.annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        self.product2a, _ = Product.objects.get_or_create(
            name='Product 2A',
            code='product2a',
            category=self.product_category_a,
            vendor_sku='some_vendor_sku',
            version=self.product_version_pro,
            plan=self.annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )
        self.product3a, _ = Product.objects.get_or_create(
            name='Product 3A',
            code='product3a',
            category=self.product_category_a,
            vendor_sku='some_vendor_sku',
            version=self.product_version_pro,
            plan=self.annual_monthly_product_plan,
            type=ProductType.SUBSCRIPTION,
            tier_number=100,
            tier_name='1-100',
        )

        # Features belong only to one product category.
        self.product_category_feature_1, _ = ProductFeature.objects.get_or_create(
            name='product_category_feature_1',
            product_category=self.product_category_a,
        )
        FeatureProductCategory.objects.get_or_create(
            product_category=self.product_category_a,
            feature=self.product_category_feature_1,
            detail='product category feature 1 detail description',
            bold=True,
            position=1
        )
        self.product_category_feature_2, _ = ProductFeature.objects.get_or_create(
            name='product_category_feature_2',
            product_category=self.product_category_a,
        )
        FeatureProductCategory.objects.get_or_create(
            product_category=self.product_category_a,
            feature=self.product_category_feature_2,
            detail='product category feature 2 detail description',
            bold=False,
            position=2
        )
        # Features belong only to PRO product version.
        self.version_feature_1, _ = ProductFeature.objects.get_or_create(
            name='version_feature_1',
            product_category=self.product_category_a,
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_pro,
            feature=self.version_feature_1,
            detail='version feature 1 detail description',
            bold=True,
            position=1
        )
        self.version_feature_2, _ = ProductFeature.objects.get_or_create(
            name='version_feature_2',
            product_category=self.product_category_a,
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_pro,
            feature=self.version_feature_2,
            detail='version feature 2 detail description',
            bold=False,
            position=2
        )
        # Features belong only to BASIC product version.
        self.version_feature_3, _ = ProductFeature.objects.get_or_create(
            name='version_feature_3',
            product_category=self.product_category_a,
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_basic,
            feature=self.version_feature_3,
            detail='version feature 3 detail description',
            bold=True,
            position=1
        )
        self.version_feature_4, _ = ProductFeature.objects.get_or_create(
            name='version_feature_4',
            product_category=self.product_category_a,
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_basic,
            feature=self.version_feature_4,
            detail='version feature 4 detail description',
            bold=False,
            position=2
        )
        # Featury belong to both PRO and BASIC product versions and product
        # category.
        self.common_feature_1, _ = ProductFeature.objects.get_or_create(
            name='common_feature_1',
            product_category=self.product_category_a,
        )
        FeatureProductCategory.objects.get_or_create(
            product_category=self.product_category_a,
            feature=self.common_feature_1,
            detail='common feature 1 detail description',
            bold=False,
            position=1
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_basic,
            feature=self.common_feature_1,
            detail='common feature 1 detail description',
            bold=False,
            position=1
        )
        FeatureVersion.objects.get_or_create(
            version=self.product_version_pro,
            feature=self.common_feature_1,
            detail='common feature 1 detail description',
            bold=False,
            position=1
        )

        self.catalog, _ = Catalog.objects.get_or_create(name='catalog')
        ProductCatalog.objects.get_or_create(
            product=self.product1a,
            catalog=self.catalog,
            defaults={
                'product': self.product1a,
                'catalog': self.catalog,
                'price': 99.99,
                'alternate_price': 199.99
            }
        )
        ProductCatalog.objects.get_or_create(
            product=self.product2a,
            catalog=self.catalog,
            defaults={
                'product': self.product2a,
                'catalog': self.catalog,
                'price': 10.00,
                'alternate_price': 15.00
            }
        )
        ProductCatalog.objects.get_or_create(
            product=self.product3a,
            catalog=self.catalog,
            defaults={
                'product': self.product3a,
                'catalog': self.catalog,
                'price': 1.00,
                'alternate_price': 0.99
            }
        )

        self.customer = Customer.objects.get(name='test-2.com')
        # self.subscription = self.customer.subscription_set \
        #     .order_by('created_at') \
        #     .first()
        self.subscription = SubscriptionFactory(
            customer=self.customer,
            product=self.product1a,
            catalog=self.catalog,
            plan=self.annual_yearly_product_plan,
            vendor_plan=self.annual_yearly_product_plan,
            created_at=datetime.now()
        )
        self.client.force_authenticate(
            user=self.subscription.customer.users.first().auth_user
        )
        create_display_products_from_product(self.product1a)
        create_display_products_from_product(self.product2a)
        create_display_products_from_product(self.product3a)

    def test_api(self):
        response = self.client.get(
            reverse('new_frontend:list_pricing_plans_view'),
            {
                'product_category_id': self.product_category_a.id,
                'order_type': 'new'
            }
        )
        self.assertEquals(response.status_code, 200, 'Invalid response status.')
        data = json.loads(response.content)
        rendered_product_category_feature_ids = [item['id'] for item in data['features']]
        rendered_product_category_feature_ids.sort()
        original_product_category_feature_ids = list(
            FeatureProductCategory.objects.filter(
                product_category=self.subscription.product.category.id
            )
            .values_list('feature', flat=True)
        )
        original_product_category_feature_ids.sort()
        self.assertEquals(
            rendered_product_category_feature_ids,
            original_product_category_feature_ids,
            'Product features is not match subscription product category.'
        )
        rendered_plan_names = [item['name'] for item in data['plans']]
        rendered_plan_names.sort()
        original_plan_names = [product.plan.name for product in self.product_category_a.products.all().distinct('plan')]
        original_plan_names.sort()
        self.assertEquals(
            rendered_plan_names,
            original_plan_names,
            'Plans names do not match.'
        )
        self.assertEqual(len(data['plans']), 1, 'Should be only one plan.')
        self.assertEqual(len(data['plans'][0]['versions']), 1, 'Should be only one version.')
        rendered_versions = data['plans'][0]['versions']
        rendered_products = data['plans'][0]['versions'][0]['products']
        rendered_product_names = [product['name'] for product in rendered_products]
        rendered_product_names.sort()
        self.assertEqual(
            rendered_product_names,
            [self.product1a.name, self.product2a.name, self.product3a.name],
            'Products do not match.'
        )
        rendered_features = data['plans'][0]['versions'][0]['features']
        rendered_features_ids = [feature['id'] for feature in rendered_features]
        rendered_features_ids.sort()
        original_features_ids = list(
            self.product_version_pro.feature_options
            .all()
            .values_list('feature', flat=True)
        )
        original_features_ids.sort()
        self.assertEqual(
            rendered_features_ids,
            original_features_ids,
            'Features do not match.'
        )
