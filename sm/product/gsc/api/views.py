from __future__ import absolute_import

import logging

from django.conf import settings
from django.db import transaction
from django.http import Http404
from rest_framework import mixins, serializers, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from sm.core.signals import subscription_updated
from sm.product.gsc import models
from sm.test.models import get_test_vendor_profile

logger = logging.getLogger(__name__)


class ProductSerializer(serializers.Serializer):
    version = serializers.CharField(required=True)


class SubscriptionSerializer(serializers.Serializer):
    domain = serializers.CharField()
    install_date = serializers.DateTimeField(required=True)
    next_invoice_date = serializers.DateTimeField(required=True)
    expiry_date = serializers.DateTimeField(required=True)
    vendor_status = serializers.CharField(required=True)
    vendor_licenses = serializers.IntegerField(required=True)
    # if is cancelled, renewal_option => CANCELLED else RENEW
    renewal_option = serializers.CharField(required=True)

    ## the following are saved in other tables
    profile_id = serializers.CharField(write_only=True, allow_blank=True)
    txn_id = serializers.CharField(write_only=True, allow_blank=True)
    catalog_id = serializers.IntegerField(write_only=True)

    non_member_fields = ['profile_id', 'txn_id', 'catalog_id']

    def to_representation(self, instance):
        return super(SubscriptionSerializer, self).to_representation(instance)

    def update(self, instance, validated_data):
        """

        :type instance: models.Subscription
        """
        update_crm = check_status = False
        if 'vendor_status' in validated_data:
            update_crm = (str(instance.vendor_status) != validated_data['vendor_status'])
            # if status is expired, decide new status with current subscription
            if validated_data['vendor_status'] == 'EXPIRED':
                check_status = True

        for k in validated_data:
            if k not in self.non_member_fields and validated_data[k]:
                setattr(instance, k, validated_data[k])

        if check_status:
            if instance.expired:
                # Use exists() instead of count or even just filter
                if models.OrderDetail.objects.filter(subscription=instance).count() == 0:
                    instance.vendor_status = models.VendorStatus.EXPIRED_EVAL
                else:
                    instance.vendor_status = models.VendorStatus.EXPIRED_PAID
            else:
                if models.OrderDetail.objects.filter(subscription=instance).count() == 0:
                    instance.vendor_status = models.VendorStatus.EVAL
                else:
                    instance.vendor_status = models.VendorStatus.PAID

        profile_id = validated_data.get('profile_id', None)
        txn_id = validated_data.get('txn_id', None)
        catalog_id = validated_data.get('catalog_id', None) or models.get_default_catalog().oid
        vendor_licenses = validated_data.get('vendor_licenses', None)

        if profile_id and txn_id and catalog_id and vendor_licenses:
            txn = models.create_transaction_from_gsc(profile_id, txn_id,
                                                     catalog_id,
                                                     instance.customer,
                                                     vendor_licenses)
            instance.order = txn.order
            instance.product = txn.order.details.first().product

            if profile_id.lower().startswith('fake-sid'):
                instance.renewal_option = models.RenewalOption.CANCEL

        if catalog_id:
            instance.catalog = models.Catalog.objects.get(oid=catalog_id)

        instance.save()

        if check_status:
            subscription_updated.send(models.Subscription, instance=instance)

        if update_crm:
            from sm.product.gsc.zoho import update_account
            update_account(instance.customer.get_communication_user(), delay=10)

        return instance

    def get_txn(self, obj):
        if obj.order:
            return models.PaypalTransaction.objects.filter(order=obj.order).first()

    def get_profile_id(self, obj):
        txn = self.get_txn(obj)
        if txn:
            return txn.profile_id

    def get_txn_id(self, obj):
        txn = self.get_txn(obj)
        if txn:
            return txn.txn_id

    def get_catalog_id(self, obj):
        return obj.catalog.oid


class SubscriptionDetailView(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = [IsAdminUser]
    serializer_class = SubscriptionSerializer

    def get_object(self):
        # TODO(greg_eremeev) LOW: need to use get_object_or_404 and consider an opportunity to define queryset parameter
        customer_name = self.kwargs['customer']
        try:
            return models.Subscription.objects.get(
                product__category=models.get_gsc_product_category(),
                customer__name=customer_name
            )
        except models.Subscription.DoesNotExist:
            raise Http404

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super(SubscriptionDetailView, self).update(request, *args, **kwargs)


class AccountSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")
    email = serializers.ReadOnlyField()  # can be updated through argument

    def get_initial(self):
        return super(AccountSerializer, self).get_initial()

    class Meta:
        model = models.User
        fields = ('customer', 'name', 'email', 'contact_email', 'phone_number', 'id')


class ProfileSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")

    def save(self, **kwargs):
        instance = super(ProfileSerializer, self).save(**kwargs)
        models.ProfileClazz.objects.get_or_create(
            profile=instance,
            product_clazz=models.PRODUCT_CLAZZ
        )

        return instance

    class Meta:
        model = models.Profile


class VendorProfileSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.name")
    name = serializers.ReadOnlyField()

    def save(self, **kwargs):
        from sm.product.gsc import zoho
        update_crm = False
        kwargs['name'] = self.instance.customer.name
        if settings.TEST_MODE:
            instance = super(VendorProfileSerializer, self) \
                .save(**get_test_vendor_profile(self.instance.customer.name))
        else:
            instance = super(VendorProfileSerializer, self).save(**kwargs)
        assert isinstance(instance, models.VendorProfile)
        models.VendorProfileClazz.objects.get_or_create(
            vendor_profile=instance,
            product_clazz=models.PRODUCT_CLAZZ
        )

        # check if the subscription is there for customer
        subscription = models.SubscriptionManager(instance.customer).ensure_exists()

        # temporary fix: update crm when number of user changes
        if subscription.billable_licenses != instance.users:
            update_crm = True

        # temporary fix: update crm when account doesn't exists
        record = zoho.get_zoho_customer_record(self.instance.customer)
        if not record or not record.account_id:
            update_crm = True

        subscription.billable_licenses = instance.users
        subscription.save()

        if update_crm:
            zoho.convert_lead(self.instance.customer.get_communication_user())

        return instance

    class Meta:
        model = models.VendorProfile


class UpdateRetrieveGenericView(viewsets.GenericViewSet,
                                mixins.UpdateModelMixin,
                                mixins.RetrieveModelMixin):
    def is_retrieve_request(self):
        return self.request.method.lower() == 'get'


class VendorProfileUpdateView(UpdateRetrieveGenericView):
    permission_classes = [IsAdminUser]
    serializer_class = VendorProfileSerializer

    def validate_customer(self, request):
        customer_name = self.kwargs['customer']
        try:
            return models.Customer.objects.get(
                name=customer_name
            )
        except models.Customer.DoesNotExist:
            raise NotFound("Customer %s is not found" % customer_name)

    def get_object(self):
        customer = self.validate_customer(self.request)

        try:
            return models.VendorProfileClazz.objects.get(
                vendor_profile__customer=customer, product_clazz=models.PRODUCT_CLAZZ
            ).vendor_profile
        except models.VendorProfileClazz.DoesNotExist:
            if self.is_retrieve_request():
                raise Http404
            self.request.new_instance = True
            return models.VendorProfile(customer=customer)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            kwargs['partial'] = True
            resp = super(VendorProfileUpdateView, self).update(request, *args, **kwargs)
            if hasattr(self.request, 'new_instance'):
                resp.status_code = 201

            return resp


class ProfileUpdateView(UpdateRetrieveGenericView):
    permission_classes = [IsAdminUser]
    serializer_class = ProfileSerializer

    def validate_customer(self, request):
        customer = self.kwargs['customer']
        customer, _ = models.Customer.objects.get_or_create(
            name=customer
        )

        return customer

    def get_object(self):
        customer = self.validate_customer(self.request)

        try:
            return models.ProfileClazz.objects.get(
                profile__customer=customer, product_clazz=models.PRODUCT_CLAZZ
            ).profile
        except models.ProfileClazz.DoesNotExist:
            if self.is_retrieve_request():
                raise Http404
            self.request.new_instance = True
            return models.Profile(customer=customer)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            kwargs['partial'] = True
            resp = super(ProfileUpdateView, self).update(request, *args, **kwargs)
            if hasattr(self.request, 'new_instance'):
                resp.status_code = 201

            return resp


class AccountUpdateView(UpdateRetrieveGenericView):
    permission_classes = [IsAdminUser]
    serializer_class = AccountSerializer

    def validate_customer(self, request):
        customer = self.kwargs['customer']
        customer, _ = models.Customer.objects.get_or_create(
            name=customer
        )

        return customer

    def get_object(self):
        customer = self.validate_customer(self.request)
        email = self.kwargs.get('email')

        try:
            user = models.User.objects.get(email=email, customer=customer)
        except models.User.DoesNotExist:
            if self.is_retrieve_request():
                logger.info("User %s is not found in %s", email, customer)
                raise Http404
            user = models.User(email=email, customer=customer)
            self.request.new_user = True
        return user

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            resp = super(AccountUpdateView, self).update(request, *args, **kwargs)
            if hasattr(self.request, 'new_user'):
                resp.status_code = 201

            return resp


class FirstShareView(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        """

        :type request: Request
        """
        domain = request.query_params.get('domain')
        customer = models.Customer.objects.filter(name=domain).first()
        updated = False
        if customer:
            if customer.install_status != 'Shared':
                from sm.product.gsc import zoho
                customer.install_status = 'Shared'
                customer.save()
                zoho.update_account(customer.get_communication_user())
                updated = True
        else:
            logger.warn("No domain found %s", domain)

        return Response(dict(success=updated))
