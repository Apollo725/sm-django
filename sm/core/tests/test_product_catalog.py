from collections import namedtuple
from unittest import skip

from django.test import TestCase

from sm.core.models import Product, ProductVersionEnum, ProductType, ProductCatalog, Catalog


class ProductCatalogTest(TestCase):

    DATA_TUPLE = namedtuple('TestData', ('product_tier_low', 'product_tier_high', 'product_catalog_price'))
    TEST_DATA = {'low': DATA_TUPLE(1, 5, 50.0), 'medium': DATA_TUPLE(6, 10, 100.0), 'high': DATA_TUPLE(11, 20, 200.0)}

    @staticmethod
    def _create_product(tier_low, tier_high):
        return Product.objects.create(
            name='GSC Professional Version ({}-{}) Users'.format(tier_low, tier_high),
            version=ProductVersionEnum.PRO, type=ProductType.SUBSCRIPTION,
            tier_number=tier_high, tier_name='{} - {}'.format(tier_low, tier_high),
            code='gsc_pro_{}-{}'.format(tier_low, tier_high))

    def _add_product(self, catalog, data_tuple):
        product = self._create_product(data_tuple.product_tier_low, data_tuple.product_tier_high)
        ProductCatalog.objects.create(price=data_tuple.product_catalog_price, catalog=catalog, product=product)

    def _add_products(self, catalog):
        for data_tuple in self.TEST_DATA.values():
            self._add_product(catalog, data_tuple)

    @skip("model changed")
    def test_tier(self):
        catalog = Catalog.objects.create(default=True, name='GSC USD Standard prices')
        self._add_products(catalog)

        data_low_price = self.TEST_DATA['low']
        tier = catalog.get_tier(data_low_price.product_tier_high)

        self.assertEquals(data_low_price.product_tier_high, tier.high)
        self.assertEquals(data_low_price.product_tier_low, tier.low)

        data_medium_price = self.TEST_DATA['medium']
        tier = catalog.get_tier(data_medium_price.product_tier_high)

        self.assertEquals(data_medium_price.product_tier_high, tier.high)
        self.assertEquals(data_medium_price.product_tier_low, tier.low)

        data_high_price = self.TEST_DATA['high']
        tier = catalog.get_tier(data_high_price.product_tier_high)
        self.assertEquals(data_high_price.product_tier_high, tier.high)
        self.assertEquals(data_high_price.product_tier_low, tier.low)

        tier = catalog.get_tier(200)
        self.assertEquals(data_high_price.product_tier_high, tier.high)
