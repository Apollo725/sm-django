from sm.core.predefined_constants import GOOGLE_VENDOR_NAME, GSUITE_PRODUCT_CATEGORY_CODE
from sm.product.gsc.models import Subscription, Vendor, Product, ProductCategory, \
    SubscriptionPlan as SMPlanName, SubscriptionPaymentMethod as \
    SMPaymentMethod, RenewalOption as SMRenewalOption, \
    SubscriptionStatus as SubscriptionStatus, VendorField, VendorValue, VendorStatus
from sm.product.google.models import PlanName as GooglePlanName, \
    RenewalType as GoogleRenewalType

from . import policy
from .general_utils import format_date, flatten_dict
from ..decorators import log_time

import logging

logger = logging.getLogger(__name__)

GSUITE_PRODUCT_CATEGORY = ProductCategory.objects.filter(code=GSUITE_PRODUCT_CATEGORY_CODE).first()


# todo: deprecate
def _translate_plan_name(google_plan_name):
    if not google_plan_name:
        return None
    if google_plan_name == GooglePlanName.ANNUAL_MONTHLY_PAY:
        return SMPlanName.ANNUAL_MONTHLY
    elif google_plan_name == GooglePlanName.ANNUAL_YEARLY_PAY:
        return SMPlanName.ANNUAL_YEARLY
    elif google_plan_name == GooglePlanName.FLEXIBLE:
        return SMPlanName.FLEXIBLE
    return None


def _get_product(sku_id=None, vendor_plan=SMPlanName.UNKNOWN_PLAN):
    if sku_id is None:
        raise ValueError('Please specify an sku_id param')

    product = Product.objects.filter(vendor_sku=sku_id, plan=vendor_plan).first()
    if not product:
        logger.error("No Product matched for sku")
        return None

    return product


def __translate_billing_method(billing_method):
    if not billing_method:
        return SMPaymentMethod.OFFLINE
    return None


def _translate_renewal_option(renewal_option):
    if not renewal_option:
        return None
    elif renewal_option in (GoogleRenewalType.AUTO_RENEW_MONTHLY_PAY,
                            GoogleRenewalType.AUTO_RENEW_YEARLY_PAY,
                            GoogleRenewalType.RENEW_CURRENT_USERS_MONTHLY_PAY,
                            GoogleRenewalType.RENEW_CURRENT_USERS_YEARLY_PAY):
        return SMRenewalOption.RENEW
    elif renewal_option == GoogleRenewalType.CANCEL:
        return SMRenewalOption.CANCEL


def _adjust_vendor_status_for_trial(vendor_status):
    if vendor_status == VendorStatus.PAID:
        return VendorStatus.EVAL
    elif vendor_status == VendorStatus.EXPIRED_PAID:
        return VendorStatus.EXPIRED_EVAL
    return vendor_status


# todo should we @log_time
def sync_google_subscriptions(new_subscriptions):
    """ This function synchronizes list of google subscriptions with sm_subscriptions
        Two subscriptions will be matched if customer and product are matched.
        Unmatched old subscriptions are deleted
        :rtype list
        """
    if new_subscriptions is None:
        return None

    customer = new_subscriptions[0]['customer']
    vendor = Vendor.objects.get(name=GOOGLE_VENDOR_NAME)

    # gsuite_sub = (sub for sub in new_subscriptions if 'G Suite' in sub['product'].name).next()

    logger.debug("Synchronizing subscriptions for {}".format(customer.name))
    new_sm_subs = list()
    for sub_dict in new_subscriptions:
        logger.debug(sub_dict['product'])
        # Shouldn't fail, cannot have a customer with two identical products.
        # Will update the subscription with the same customer and product like the new one
        sub, created = Subscription.objects. \
            update_or_create(defaults=sub_dict,
                             customer=customer,
                             product=sub_dict['product'])
        new_sm_subs.append(sub)

    Subscription.objects.filter(customer=customer, product__category__vendor=vendor).exclude(
        id__in=[sm_sub.id for sm_sub in new_sm_subs]).delete()

    # update parent_subscription and billable_licenses
    gsuite_sub = (sub for sub in new_sm_subs if sub.product.category == GSUITE_PRODUCT_CATEGORY).next()
    # gsuite_sub = Subscription.objects.filter(customer=customer, product__category=GSUITE_PRODUCT_CATEGORY).first()
    for sub in new_sm_subs:
        if sub == gsuite_sub:
            sub.billable_licenses = sub.vendor_licenses
            pass
        else:
            sub.parent_subscription = gsuite_sub
            sub.billable_licenses = gsuite_sub.vendor_licenses
            sub.save()

    # update subs in zoho

    return new_sm_subs


def check_eligibility(google_json):
    """This function checks if json subscriptions are eligible for transfer
    :rtype boolean
    """
    if 'subscriptions' not in google_json:
        return False

    for subscription in google_json['subscriptions']:
        if 'G Suite' in subscription['skuName']:
            if subscription['plan']['planName'] in ['ANNUAL_YEARLY_PAY']:
                logger.info(
                    'Subscription plan {} not matching,'
                    ' not eligible for {}'.
                    format(subscription['plan']['planName'],
                           subscription['customerDomain']))
                return False
            return True
    return False


@log_time
def parse_google_json(google_json, data):
    subs_list = list()
    sub_dict = dict()
    vendor = Vendor.objects.get(name=GOOGLE_VENDOR_NAME)

    for sub in google_json:
        subscription = flatten_dict(sub)
        # do not create subscriptions with no licenses
        if 'seats.licensedNumberOfSeats' not in subscription or not subscription['seats.licensedNumberOfSeats']:
            continue

        for key in subscription:
            logger.debug(key)
            vendor_field = VendorField.objects.filter(
                vendor=vendor,
                vendor_name=key
            )
            vendor_value = VendorValue.objects.filter(
                field=vendor_field,
                vendor_value=subscription[key]
            )
            if vendor_field and not vendor_value:
                logger.debug("no value, key: {} - {}".format(key, subscription[key]))
                # iteration in case on json field is assigned to multiple sm fields
                for field in vendor_field:
                    # If the key has time in it we parse it to get a datetime object
                    if 'Time' in key:
                        tlog = sub_dict[field.sm_name] = format_date(subscription[key])
                        logger.debug(tlog)
                    else:
                        sub_dict[field.sm_name] = subscription[key]
            elif vendor_value and vendor_value:
                sub_dict[vendor_field[0].sm_name] = vendor_value[0].sm_value

        customer = data['customer']
        sub_dict['customer'] = customer
        sub_dict['invoiced_customer'] = customer
        sub_dict['status'] = SubscriptionStatus.DETECTED
        if sub_dict['vendor_trial']:
            sub_dict['vendor_status'] = _adjust_vendor_status_for_trial(sub_dict['vendor_status'])

        sub_dict['vendor_console'] = policy.get_vendor_console(customer)
        sub_dict['currency'] = currency = policy.get_customer_currency(customer)
        sub_dict['catalog'] = policy.get_customer_catalog(customer, currency=currency)

        if 'vendor_plan' in sub_dict:
            logger.debug("The translated plan name is {}".format(sub_dict['vendor_plan']))
        else:
            sub_dict['vendor_plan'] = 'UNKNOWN_PLAN'
        product = _get_product(sub['skuId'], sub_dict['vendor_plan'])
        sub_dict['product'] = product

        sub_dict['name'] = "{} for {}".format(product.category.name, customer.name)
        sub_dict['vendor_product'] = sub_dict['product']
        sub_dict['payment_method'] = ''

        # manage possible issues with missing license / user counts
        if 'vendor_users' not in sub_dict.keys():
            logger.warn('Number of users not received. Going to record 0 users')
            sub_dict['vendor_users'] = 0
        if 'vendor_licenses' not in sub_dict.keys():
            sub_dict['licenses'] = sub_dict['vendor_licenses'] = sub_dict['vendor_users']
        if 'billable_licenses' not in sub_dict.keys():
            sub_dict['billable_licenses'] = sub_dict['vendor_users']

        # prevent defaults and set empty fields
        sub_dict['plan'] = ''
        sub_dict['renewal_option'] = ''

        # set sm subscription license field to be the same like vendor one at this point
        sub_dict['licenses'] = sub_dict['vendor_licenses']

        subs_list.append(sub_dict)
        sub_dict = dict()

    return subs_list


def get_zoho_products_list_from_response(response):
    if response is None or response.data is None:
        return None, None
    ids = [dict(data)['id'] for data in response.data]
    if ids:
        subscriptions = Subscription.objects.filter(id__in=ids).all()
        if subscriptions:
            customer = subscriptions[0].customer
            return customer, get_zoho_products_list(subscriptions)
    return None, None


def get_zoho_products_list(subscriptions):
    vendor_products = dict({
        'GSUITE_BASIC': '',
        'GSUITE_BUSINESS': '',
        'GSUITE_STANDARD': '',
        'GSUITE_ENTERPRISE': '',
        'GSUITE_LITE': '',
        'GSUITE_EDUCATION': '',
        'GAMS': '',
        'GDR_20GB': '',
        'GDR_50GB': '',
        'GDR_200GB': '',
        'GDR_400GB': '',
        'GDR_1TB': '',
        'GDR_2TB': '',
        'GDR_4TB': '',
        'GDR_8TB': '',
        'GDR_16TB': '',
        'GV': '',
        'GV_FE': '',
        'CDM': ''
    })
    for subscription in subscriptions:
        product_code = subscription.product.code
        for key in vendor_products:
            if product_code and product_code.startswith(key):
                # this will work good except for GV and GV_FE which both start with GV
                if key == 'GV' and product_code.startswith('GV_FE'):
                    continue
                vendor_products.update({key: subscription.vendor_licenses})
                break
    logger.info("Will update zoho account for customer {} with this data: {}".
                 format(subscriptions[0].customer.name, vendor_products))
    return vendor_products
