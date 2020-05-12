import logging

from rest_framework import serializers

from sm.new_frontend.subscriptions.serializer_helpers import *
from sm.product.gsc import models
from sm.product.google.utility.subscriptions_utility import policy


logger = logging.getLogger(__name__)


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('_name_serialize', read_only=True)
    image_url = serializers.SerializerMethodField('_image_url_serialize', read_only=True)

    class Meta:
        model = models.Product
        fields = ("name", "version", "plan", "app_url", 'image_url')

    @staticmethod
    def _name_serialize(obj):
        return obj.category.name if obj.category else None

    @staticmethod
    def _image_url_serialize(obj):
        return product_image_url(obj)


class CatalogSerializer(serializers.ModelSerializer):
    unit_cost = serializers.FloatField(read_only=True)
    unit = serializers.CharField(read_only=True)

    class Meta:
        model = models.Catalog
        fields = ('id', 'unit_cost', 'unit')


class ChildProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField('_image_url_serialize', read_only=True)

    class Meta:
        model = models.Product
        fields = ("id", "name", "version", "plan", "image_url")

    @staticmethod
    def _image_url_serialize(obj):
        return product_image_url(obj)


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BraintreePaymentMethod
        fields = ("type", "card_type", "last_4_digits", "email_address")


class ChildCatalogSerializer(serializers.ModelSerializer):
    unit_price = serializers.FloatField(read_only=True)
    per_user = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Catalog
        fields = ('id', 'unit_price', 'per_user',)


class ChildSubscriptionSerializer(serializers.ModelSerializer):
    product = ChildProductSerializer(many=False, read_only=True)
    catalog = serializers.SerializerMethodField('_catalog_serialize', read_only=True)

    class Meta:
        model = models.Subscription
        fields = ('id',
                  'product',
                  'vendor_licenses',
                  'catalog',
                  )

    @staticmethod
    def _catalog_serialize(obj):
        unit_cost = obj.product.get_price(obj.catalog)
        return ChildCatalogSerializer({"id": obj.catalog.id,
                                       "unit_price": unit_cost,
                                       "per_user": catalog_per_user(obj)}, many=False).data


class SubscriptionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False, read_only=True)
    catalog = serializers.SerializerMethodField('_catalog_serialize', read_only=True)
    payment_method = serializers.SerializerMethodField('_payment_method_serialize', read_only=True)
    child_subscriptions = serializers.SerializerMethodField('_list_child_subscriptions', read_only=True)
    billing_frequency = serializers.SerializerMethodField('_billing_frequency', read_only=True)
    used_licenses = serializers.SerializerMethodField('_used_licenses', read_only=True)
    purchased_licenses = serializers.SerializerMethodField('_purchased_licenses', read_only=True)
    total_users = serializers.SerializerMethodField('_total_users', read_only=True)

    class Meta:
        model = models.Subscription
        fields = ('id',
                  'promotion_banner',
                  'unbound',
                  'product',
                  'domain',
                  'used_licenses',
                  'purchased_licenses',
                  'total_users',
                  'vendor_status',
                  'catalog',
                  'currency',
                  'billing_frequency',
                  'start_plan_date',
                  'expiry_date',
                  'next_invoice_date',
                  'renewal_option',
                  'payment_method',
                  'child_subscriptions'
                  )

    @staticmethod
    def _catalog_serialize(obj):
        unit_cost = obj.product.get_price(obj.catalog)
        return CatalogSerializer({"id": obj.catalog.id,
                                  "unit_cost": unit_cost,
                                  "unit": catalog_unit(obj)}, many=False).data

    def _payment_method_serialize(self, obj):
        customer = self._context['request'].user.sm.customer
        methods = models.get_payment_methods_offline(customer)
        return PaymentSerializer(get_payment_method(methods), many=False).data

    def _list_child_subscriptions(self, obj):
        list_type = self._context['request'].GET.get('layout', 'list')

        if list_type in ('list', 'encapsulate'):
            if list_type == 'list' or obj.children.count() == 0:
                return None
        else:
            raise serializers.ValidationError('List_type value was invalid')

        return serializers.ListSerializer(obj.children, child=ChildSubscriptionSerializer()).data

    @staticmethod
    def _billing_frequency(obj):
        # product = obj.product
        # if product and product.plan:
        #     return product.plan.billing_frequency
        # return ""
        # todo: the models needed are on Vadims pricing branch
        return "todo"

    @staticmethod
    def _used_licenses(obj):
        return obj.vendor_users

    @staticmethod
    def _purchased_licenses(obj):
        return obj.licenses

    @staticmethod
    def _total_users(obj):
        return obj.billable_licenses


class UpsertSubscriptionSerializer(serializers.ModelSerializer):
    vendor_sku = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        vendor_sku = validated_data['vendor_sku']
        if vendor_sku == "":
            logger.warn("Cannot create a subscription without vendor_sku for: {}".format(validated_data['domain']))
            return None
         # subscription = get_subscription_by_product_category(validated_data)
        customer = Customer.objects.filter(name=validated_data['domain']).first()
        logger.debug("Found customer {} for domain name {}".format(customer, validated_data['domain']))
        product = Product.objects.filter(vendor_sku=vendor_sku,
                                         plan=models.SubscriptionPlan.UNKNOWN_PLAN).first()
        if not product:
            logger.error("Cannot match a product for vendor_sku = {}".format(vendor_sku))
            return None

        subscription = Subscription.objects.filter(customer=customer, product=product).first()
        kwargs = dict(
            name="%s for %s" % (product.code, customer.name),
            status=models.SubscriptionStatus.DETECTED.value,
            vendor_status='',
            saw_price=False,
            vendor_licenses=validated_data['vendor_licenses'],
            vendor_users=validated_data['vendor_licenses'],
            domain=validated_data['domain'],
            customer=customer,
            product=product)

        if subscription is not None and subscription.unbound:
            subscription, _ = Subscription.objects.update_or_create(kwargs, id=subscription.id)
        if subscription is None:
            category_detect(validated_data)
            subscription = Subscription.objects.create(
                billable_licenses=0,
                catalog=policy.get_customer_catalog(customer),
                **kwargs
            )
        return subscription

    class Meta:
        model = models.Subscription
        fields = ('vendor_licenses', 'domain', 'vendor_sku', "status", "id")
