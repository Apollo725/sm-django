from rest_framework import serializers

from sm.product.gsc import models


class ProductFeatureSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='feature.id')
    name = serializers.CharField(source='feature.name')
    detail = serializers.CharField()
    bold = serializers.BooleanField()
    position = serializers.IntegerField()

    class Meta:
        fields = ['id', 'name', 'detail', 'bold', 'position']


class DisplayProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='displayed_product.name')
    tier_number = serializers.IntegerField(source='displayed_product.tier_number')
    tier_name = serializers.CharField(source='displayed_product.tier_name')
    enabled = serializers.BooleanField()
    highlighted = serializers.BooleanField()
    bigger = serializers.SerializerMethodField()
    smaller = serializers.SerializerMethodField()

    product_catalog_cache = {}

    class Meta:
        model = models.DisplayProduct
        fields = [
            'name', 'tier_number', 'tier_name', 'enabled', 'highlighted',
            'bigger', 'smaller'
        ]

    def get_product_catalog(self, instance):
        """
        In get_bigger and get_smaller we need product catalog instance and we
        make two identical reques. So to boost performence we caching product
        catalog instanse.
        """
        product_id = instance.displayed_product.id
        product_catalog = self.product_catalog_cache.get(product_id)
        if product_catalog is None:
            product_catalog = models.ProductCatalog.objects.get(
                product=instance.displayed_product,
                catalog=self.context['catalog']
            )
            self.product_catalog_cache[product_id] = product_catalog
        return product_catalog

    def get_bigger(self, instance):
        product_catalog = self.get_product_catalog(instance)

        if instance.showcase_alternate:
            price = product_catalog.alternate_price
            frequency = instance.displayed_product.plan.alternate_frequency
        else:
            price = product_catalog.price
            frequency = instance.displayed_product.plan.billing_frequency

        return {
            'price': price,
            'frequency': frequency,
            'unit': instance.displayed_product.unit,
            'unit_plural': instance.displayed_product.unit_plural,
        }

    def get_smaller(self, instance):
        if not instance.show_small:
            return {}

        product_catalog = self.get_product_catalog(instance)

        if instance.showcase_alternate:
            price = product_catalog.price
            frequency = instance.displayed_product.plan.billing_frequency
        else:
            price = product_catalog.alternate_price
            frequency = instance.displayed_product.plan.alternate_frequency
        return {
            'price': price,
            'frequency': frequency,
            'unit': instance.displayed_product.unit,
            'unit_plural': instance.displayed_product.unit_plural,
        }


class ProductVersionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    extended_name = serializers.CharField(read_only=True)
    motto = serializers.CharField(read_only=True)
    color = serializers.CharField(source='color_code', read_only=True)
    products = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductVersion
        fields = [
            'name', 'extended_name', 'motto', 'color', 'products', 'features'
        ]

    def get_products(self, instance):
        display_products = models.DisplayProduct.objects \
            .filter(
                current_product=self.context['current_product'],
                type=self.context['action_type'],
                display=True
            ) \
            .select_related('displayed_product')
        return DisplayProductSerializer(
            instance=display_products,
            many=True,
            context=self.context
        ).data

    def get_features(self, instance):
        return ProductFeatureSerializer(
            many=True,
            instance=instance.feature_options.all(),
            context=self.context
        ).data


class ProductPlanSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True)
    default = serializers.SerializerMethodField('_is_default_serialize',
                                                read_only=True)
    toggle_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    billing_frequency = serializers.CharField(read_only=True)
    commitment = serializers.CharField(read_only=True)
    versions = serializers.SerializerMethodField('_version_serialize',
                                                 read_only=True)

    class Meta:
        model = models.ProductPlan
        fields = [
            'id', 'name', 'default', 'toggle_name', 'full_name', 'description',
            'billing_frequency', 'commitment', 'versions'
        ]

    def _is_default_serialize(self, instance):
        default_plan_id = self.context['default_plan_id']
        return instance.id == default_plan_id

    def _version_serialize(self, instance):
        versions = [
            product.version for product in instance.products.distinct('version')
        ]
        return ProductVersionSerializer(
            many=True,
            instance=versions,
            context=self.context
        ).data


class PricingPlansSerializer(serializers.ModelSerializer):
    '''
    Pricing plans that used on pricing page for specific product category.
    '''
    product_category_name = serializers.CharField(source='name', read_only=True)
    logo_small = serializers.CharField(read_only=True)
    logo_big = serializers.CharField(read_only=True)
    features = serializers.SerializerMethodField('_features_serialize')
    plans = serializers.SerializerMethodField('_plans_serialize')

    class Meta:
        model = models.ProductCategory
        fields = [
            'product_category_name', 'logo_small', 'logo_big', 'features',
            'plans'
        ]

    def _features_serialize(self, instance):
        return ProductFeatureSerializer(
            many=True,
            instance=instance.feature_options.all(),
            context=self.context
        ).data

    def _plans_serialize(self, instance):
        plans = [product.plan for product in instance.products.distinct('plan')]
        return ProductPlanSerializer(
            many=True,
            instance=plans,
            context=self.context
        ).data
