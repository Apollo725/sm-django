from rest_framework import serializers
from sm.product.gsc import models


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = ("country", "state", "city", "zip_code", "address")


class UserSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField('_get_email')

    class Meta:
        model = models.User
        fields = ('name', 'email', 'phone_number')

    @staticmethod
    def _get_email(obj):
        return obj.email or obj.contact_email


class UserProfileSerializer(serializers.ModelSerializer):
    billing_details = serializers.SerializerMethodField('_billing_details_serialize')
    billing_contact = serializers.SerializerMethodField('_billing_contact_serialize')

    class Meta:
        model = models.Customer
        fields = ('billing_details', 'billing_contact', 'reseller')

    @staticmethod
    def _billing_details_serialize(obj):
        profile = models.Profile.objects.filter(customer=obj).first()
        return ProfileSerializer(profile, many=False).data

    @staticmethod
    def _billing_contact_serialize(obj):
        user = models.User.objects.filter(customer=obj).first()
        return UserSerializer(user, many=False).data

    def update(self, instance, validated_data):
        profile, _ = models.Profile.objects.get_or_create(customer=instance)
        user, _ = models.User.objects.get_or_create(customer=instance)
        models.Profile.objects.update_or_create(self.initial_data['billing_details'], pk=profile.pk)
        models.User.objects.update_or_create(self.initial_data['billing_contact'], pk=user.pk)
        instance.reseller_id = validated_data.pop('reseller')
        instance.save()
        return instance
