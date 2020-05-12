from rest_framework import serializers

from sm.api import serializers as api_serializers
from sm.core import models

OrderListSerializer = api_serializers.OrderListSerializer
OrderRetrieveSerializer = api_serializers.RetrieveOrderSerializer


class OrderDetailDetailsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    per_user = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    subscription_id = serializers.IntegerField(source='subscription.id')
    catalog_id = serializers.IntegerField(source='catalog.id')
    type = serializers.CharField()
    amount = serializers.IntegerField()
    minimal_order = serializers.IntegerField()
    sub_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    from_date = serializers.DateTimeField()
    to_date = serializers.DateTimeField()
    expiry = serializers.DateTimeField()
    status = serializers.CharField()
    extension = serializers.DecimalField(max_digits=10, decimal_places=2)
    refunded_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = models.OrderDetail
        fields = (
            'id', 'per_user', 'product', 'subscription_id', 'catalog_id',
            'type', 'amount', 'minimal_order', 'sub_total', 'discount', 'tax',
            'from_date', 'to_date', 'expiry', 'status', 'extension',
            'refunded_amount', 'total'
        )

    def get_per_user(self, instance):
        return False

    def get_product(self, instance):
        return {
            'id': instance.product.id,
            'name': instance.product.name,
        }


class OrderDetailsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    date = serializers.DateTimeField()
    conditions = serializers.CharField()
    terms = serializers.CharField()
    due_date = serializers.DateTimeField()
    currency = serializers.CharField()
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    customer_id = serializers.IntegerField(source='customer.id')
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    comment = serializers.CharField()
    order_details = serializers.SerializerMethodField()

    class Meta:
        model = models.Order
        fields = (
            'id', 'name', 'date', 'conditions', 'terms', 'due_date', 'currency',
            'discount', 'tax', 'status', 'customer_id', 'total', 'comment',
            'order_details'
        )

    def get_order_details(self, instance):
        order_details = instance.details \
            .select_related('product') \
            .select_related('catalog') \
            .select_related('subscription') \
            .all()
        return OrderDetailDetailsSerializer(
            instance=instance.details.all(),
            many=True
        ).data
