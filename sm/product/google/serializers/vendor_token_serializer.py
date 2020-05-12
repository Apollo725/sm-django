import logging

from rest_framework import serializers
from rest_framework.exceptions import APIException

from sm.core.models import Customer
from sm.product.google.utility.get_transferable_subscriptions import \
    get_transferable_subscriptions
from sm.product.google.utility.subscriptions_utility import (check_eligibility,
                                                             get_zoho_products_list,
                                                             parse_google_json,
                                                             sync_google_subscriptions)
from sm.product.gsc.zoho import update_account

from ..models import GoogleTransferToken, OrderActionChoices
from ..utility.order_util import create_orders_from_google_subscriptions

logger = logging.getLogger(__name__)


class VendorTokenSerializer(serializers.Serializer):
    transfer_token = serializers.CharField(max_length=20)
    order = serializers.ChoiceField(choices=OrderActionChoices.choices())
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects)

    def create(self, validated_data):
        customer = validated_data['customer']
        customer_name = customer.name

        returned_json = get_transferable_subscriptions(customer_name, validated_data['transfer_token'])

        if returned_json['error']:
            logger.error("Error for %s: %s", customer_name, returned_json['errorMessage'])
            raise ProcessingException("Error retrieving your subscriptions from Google")
        else:
            logger.debug('Retrieved subscriptions from Google for customer %s', customer_name)
            logger.debug(returned_json)
            # we only save the token if it is usable
            GoogleTransferToken.objects. \
                update_or_create(customer=customer, defaults={'token': validated_data['transfer_token']})

        if not check_eligibility(returned_json):
            logger.error('customer %s not eligible', customer_name)
            raise ProcessingException("Not Eligible for Google Subscriptions transfer")
        else:
            logger.info('customer %s eligible for transfer', customer_name)

        try:
            new_subscriptions = parse_google_json(returned_json['subscriptions'], validated_data)
            logger.debug('Subscription parsing finished for customer %s', customer_name)
        except KeyError as e:
            logger.error('Subscription parsing failed for customer %s: %s', customer_name, e.message)
            raise ProcessingException(e.message)

        new_subscriptions = sync_google_subscriptions(new_subscriptions)
        logger.debug('Finished google subscription sync for customer %s', customer_name)

        if not new_subscriptions:
            raise ProcessingException("No new subscriptions created")

        # SM-248 update zoho account record with subscriptions info
        vendor_products = get_zoho_products_list(new_subscriptions)
        update_account(customer, vendor_products=vendor_products)

        create_orders_from_google_subscriptions(new_subscriptions, customer)
        logger.info('Finished creating orders for customer %s', customer_name)

        return new_subscriptions


class ProcessingException(APIException):
    status_code = 500
    default_detail = "Error occurred while processing request"
