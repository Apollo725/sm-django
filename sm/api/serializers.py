from decimal import Decimal

from rest_framework import serializers

from sm.core import models
from sm.core.auth import AUTH_TOKEN_KEY
from sm.core.models import ProductVersionEnum, SubscriptionPlan
from sm.core.util.order_util import get_valid_from, get_valid_to


class ProfileSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")

    self_link = serializers.HyperlinkedIdentityField(
        view_name="api:profile-detail",
        lookup_field="customer",
        read_only=True
    )

    customerLink = serializers.HyperlinkedIdentityField(
        view_name="api:customer-detail",
        lookup_field="customer_name",
        lookup_url_kwarg="name"
    )

    class Meta:
        model = models.Profile


class VendorProfileSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")
    self_link = serializers.HyperlinkedIdentityField(
        view_name="api:vendor-profile-detail",
        lookup_field="customer",
        read_only=True
    )

    customerLink = serializers.HyperlinkedIdentityField(
        view_name="api:customer-detail",
        lookup_field="customer_name",
        lookup_url_kwarg="name"
    )

    class Meta:
        model = models.VendorProfile


class HyperLinkedViewField(serializers.HyperlinkedIdentityField):
    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        self.linked_field = kwargs.pop('linked_field')
        super(HyperLinkedViewField, self).__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, format):
        return self.reverse(view_name, request=request, format=format) \
               + "?%s=%s" % (self.lookup_field, getattr(obj, self.linked_field))


class CustomerSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False, required=False, read_only=True)
    vendor_profile = VendorProfileSerializer(many=False, required=False, read_only=True)
    self_link = serializers.HyperlinkedIdentityField(
        view_name="api:customer-detail",
        lookup_field="name"
    )

    users_link = HyperLinkedViewField(
        view_name="api:user-list",
        lookup_field='customer',
        linked_field='name'
    )

    class Meta:
        model = models.Customer


class UserSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")

    self_link = serializers.HyperlinkedIdentityField(
        view_name="api:user-detail",
        lookup_field="email"
    )

    customer_link = serializers.HyperlinkedIdentityField(
        view_name="api:customer-detail",
        lookup_field="customer_name",
        lookup_url_kwarg="name"
    )

    token_link = serializers.HyperlinkedIdentityField(
        view_name="api:user-token-detail",
        lookup_field="email"
    )

    class Meta:
        model = models.User


class EmailReadOnlyUserSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField()
    customer = serializers.ReadOnlyField(source="customer.name")

    class Meta:
        model = models.User


class UserTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    key = serializers.CharField(max_length=32)
    created_at = serializers.DateTimeField()
    expired_in = serializers.IntegerField()
    login_link = HyperLinkedViewField(
        view_name="frontend:login",
        lookup_field=AUTH_TOKEN_KEY,
        linked_field='key'
    )


class ResellerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.verbose_name

    class Meta:
        model = models.Customer
        fields = ('id', 'name')


class BaseOrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=8, decimal_places=2)
    date = serializers.DateTimeField(format='%Y-%m-%d')


class OrderListSerializer(BaseOrderSerializer):
    class Meta:
        model = models.Order
        fields = ('id', 'date', 'name', 'total', 'status')


class ProfileOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = ('address', 'state', 'country', 'zip_code', 'city')


class CustomerOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = ('id', 'profiles', 'company_name', 'name')

    profiles = ProfileOrderSerializer(source='profile_set', many=True)
    company_name = serializers.SerializerMethodField()

    def get_company_name(self, instance):
        vendor_profile = instance.vendor_profile_set.first()
        if vendor_profile:
            return vendor_profile.org_name
        else:
            return ''


class SubscriptionOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subscription
        fields = ('domain', 'product_version', 'plan', 'expiry_date', 'total')

    plan = serializers.SerializerMethodField()
    product_version = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    expiry_date = serializers.DateTimeField(format='%Y-%m-%d')

    def get_plan(self, instance):
        return dict(SubscriptionPlan.choices())[instance.plan].title().split()[1].capitalize()

    def get_total(self, instance):
        if hasattr(instance, 'order') and instance.order:
            total = instance.order.total
        else:
            total = instance.cost
        return Decimal(total).quantize(Decimal('0.01'))

    def get_product_version(self, instance):
        if hasattr(instance, 'product'):
            return dict(ProductVersionEnum.choices())[instance.product.version].title().split()[0]


class OrderDetailOrderSerializer(serializers.ModelSerializer):
    discount = serializers.DecimalField(max_digits=8, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = models.OrderDetail
        fields = ('discount', 'sub_total', 'total')


class RetrieveOrderSerializer(BaseOrderSerializer):
    class Meta:
        model = models.Order
        fields = ('id', 'date', 'customer', 'subscription', 'sub_total',
                  'tax', 'total', 'order_detail', 'status', 'number_licenses', 'valid_from', 'valid_until')

    # tax = serializers.FloatField()
    customer = CustomerOrderSerializer()
    order_detail = serializers.SerializerMethodField()
    sub_total = serializers.DecimalField(max_digits=8, decimal_places=2)
    tax = serializers.DecimalField(max_digits=8, decimal_places=2)
    subscription = serializers.SerializerMethodField()
    number_licenses = serializers.SerializerMethodField()
    valid_from = serializers.SerializerMethodField()
    valid_until = serializers.SerializerMethodField()

    def get_subscription(self, instance):
        order_detail = instance.details.first()
        if order_detail and hasattr(order_detail, 'subscription'):
            return SubscriptionOrderSerializer(order_detail.subscription).data
        else:
            return None

    def get_order_detail(self, instance):
        return OrderDetailOrderSerializer(instance.details.first()).data

    def get_number_licenses(self, instance):
        if instance.details.count() > 0:
            return instance.details.first().amount
        else:
            return 0

    def get_valid_from(self, instance):
        valid_from = get_valid_from(instance)
        if valid_from:
            return valid_from.strftime(format='%Y-%m-%d')
        else:
            return ""

    def get_valid_until(self, instance):
        valid_until = get_valid_to(instance)
        if valid_until:
            return valid_until.strftime(format='%Y-%m-%d')
        else:
            return ""


class ResellerTempAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResellerTempAccount
        exclude = ('t_stamp', 'zoho_lead_id', )
