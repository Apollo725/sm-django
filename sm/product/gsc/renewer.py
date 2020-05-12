from __future__ import absolute_import

from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from . import subscription_manager
from . import models
from django.utils import timezone
from requests import RequestException
import logging

from . import order_manager
from . import charger
from . import failed_transaction_manager
from . import zoho
from sm.core.paypal import billing_plan
from sm.core import braintree_helper
import braintree
import braintree.exceptions
import json

logger = logging.getLogger(__name__)


def format_date(date):
    date_format = "%Y-%m-%d"
    if date:
        return date.strftime(date_format)
    return ""


def renew_subscription(subscription):
    prev_expiry_date = subscription.expiry_date

    payment_method = models.find_payment_method(subscription.customer)
    if not payment_method:
        braintree_helper.sync_payment_method(subscription.customer)
        payment_method = models.find_payment_method(subscription.customer)

    error = None
    detail = None
    order = order_manager.create_renewal_order(subscription)

    if payment_method:
        assert isinstance(payment_method, models.BraintreePaymentMethod)
        try:
            bt_payment_method = braintree.PaymentMethod.find(payment_method.token)
        except braintree.exceptions.NotFoundError:
            error = "Payment method is invalid: %s" % payment_method.token
        else:
            try:
                result = charger.charge_order(order.total, bt_payment_method, order.id, subscription.customer.name)
            except:
                logger.warn("Unable to charge order for subscription {}"
                                 .format(subscription.id))
                return subscription, False, "Unable to charge order"
            if result.is_success:
                if subscription.product.plan == models.SubscriptionPlan.ANNUAL_YEARLY:
                    expiry_date = subscription.expiry_date + relativedelta(years=1)
                    while expiry_date < timezone.now():
                        expiry_date = expiry_date + relativedelta(years=1)
                else:  # subscription.product.plan == models.SubscriptionPlan.FLEX_PREPAID:
                    expiry_date = subscription.expiry_date + relativedelta(months=1)
                    while expiry_date < timezone.now():
                        expiry_date = expiry_date + relativedelta(months=1)

                order_detail = subscription_manager.on_order_paid(
                    order.details.first(),
                    expiry_date,
                    checkout_type="renewal",
                    payment_id=result.transaction.id
                )

                models.create_bt_transaction(order_detail.order, result.transaction.id)
                subscription = order_detail.subscription
                logger.info("Customer %s is renewed, expiry date %s -> %s",
                            subscription.customer, prev_expiry_date, subscription.expiry_date)
                detail = json.dumps(dict(
                    price=float(order.total),
                    expiry_date=format_date(expiry_date),
                    license_number=subscription.vendor_licenses
                ))

                models.enable_payment_method(payment_method.token)
            else:
                tx = getattr(result, 'transaction', None)
                tx_id = ("braintree:" + tx.id) if tx else "None"
                error = billing_plan.dump_errors(result)
                models.disable_payment_method(payment_method.token)
                models.create_bt_transaction(order,
                                             result.transaction.id if result.transaction else "",
                                             error=billing_plan.dump_errors(result))

                subscription.customer.set_last_payment_status(
                    outcome=error,
                    payment_id=tx_id
                )

                subscription.customer.last_payment_type = 'renewal'

                tx = failed_transaction_manager.create(
                    order, error=error
                )

                zoho.update_failed_potential(
                    order_detail=order.details.first(),
                    failed_transaction=tx,
                    checkout_type="renewal"
                )
    else:
        error = "Payment method is not found"
        subscription.customer.set_last_payment_status(
            outcome=error,
            payment_id='None'
        )
        subscription.customer.last_payment_type = 'renewal'

    if error:
        logger.warn("Failed to renew %s: %s", subscription.customer, error)
        subscription.customer.save()

        if subscription.expired:  # if subscription expires the renewal option is changed to cancel automatically
            subscription.renewal_option = models.RenewalOption.CANCEL
            subscription.save()

        else:
            # push state manually, since the account will not be updated by the expiry process
            zoho.update_account(subscription.customer)

    return subscription, error is None, error or detail


def update_last_payment_info(customer, error):
    """

    :type customer: models.Customer
    :type error: str
    """
    customer.last_payment_date = now()
    customer.last_payment_outcome = error
    customer.save()


def renew():
    logger.info("Renewing customers....")

    errors = []
    renewed = []

    today = timezone.now()

    # renewal and charge user
    # TODO: converting to a list is redundant and only creates load on the system
    for subscription in list(models.Subscription.objects.filter(
            renewal_option=models.RenewalOption.RENEW,
            expiry_date__lt=today + relativedelta(days=7),  # renew subscription in 7 days before expiry
            product__category=models.get_gsc_product_category(),
            product__plan=models.SubscriptionPlan.FLEX_PREPAID
    ).exclude(trusted=True)) + list(
        models.Subscription.objects.filter(
            renewal_option=models.RenewalOption.RENEW,
            expiry_date__lt=today + relativedelta(days=60),  # renew subscription in 60 days before expiry
            product__category=models.get_gsc_product_category(),
            product__plan=models.SubscriptionPlan.ANNUAL_YEARLY
        ).exclude(trusted=True)):
        assert isinstance(subscription, models.Subscription)
        if not subscription.product:
            logger.error("Product of subscription %s is None", subscription)
            continue

        if subscription.payment_gateway and subscription.payment_gateway.startswith('Paypal'):
            if subscription.expiry_date + relativedelta(days=8) > today:
                #  paypal could pay in the this date
                logger.info(
                    "The subscription %s is paid by paypal subscription. Renewal this one 8 days after",
                    subscription)
            else:
                errors.append(
                    [subscription.customer.name, "Paypal failed to Renew", json.dumps({
                        "plan": subscription.product.plan,
                        "version": subscription.product.version,
                        "expiry_date": format_date(subscription.expiry_date),
                        "last_payment_id": subscription.customer.last_payment_id
                    })]
                )
                subscription.renewal_option = models.RenewalOption.CANCEL
                subscription.save()

            continue

        try:
            subscription, succeed, detail = renew_subscription(subscription)
        except:
            logger.warn("Error with subscription renew: {}"
                        .format(subscription.id))
            succeed = False
            detail = "Error With subscription renew"

        if succeed:
            renewed.append([subscription.customer.name, detail])
        else:
            errors.append([subscription.customer.name, detail, json.dumps({
                "plan": subscription.product.plan,
                "version": subscription.product.version,
                "expiry_date": format_date(subscription.expiry_date),
                "last_payment_id": subscription.customer.last_payment_id
            })])

    return errors, renewed


def expire_subscriptions():
    # find expired subscriptions
    result = []
    for subscription in models.Subscription.objects.filter(
            renewal_option=models.RenewalOption.CANCEL,
            product__category=models.get_gsc_product_category(),
            expiry_date__lt=timezone.now(),
    ).exclude(vendor_status__contains="EXPIRED").exclude(trusted=True):
        status = subscription.vendor_status
        if subscription.vendor_status == models.VendorStatus.EVAL:
            subscription.vendor_status = models.VendorStatus.EXPIRED_EVAL
        elif subscription.vendor_status == models.VendorStatus.PAID:
            subscription.vendor_status = models.VendorStatus.EXPIRED_PAID
        elif subscription.vendor_status in (
                models.VendorStatus.UNINSTALLED_EVAL, models.VendorStatus.UNINSTALLED_EXPIRED,
                models.VendorStatus.UNINSTALLED_PAID):
            subscription.vendor_status = models.VendorStatus.UNINSTALLED_EXPIRED

        subscription.renewal_option = models.RenewalOption.CANCEL
        subscription.save()

        result.append([subscription.customer.name, json.dumps(dict(
            license_number=subscription.vendor_licenses,
            old_status=status,
            new_status=subscription.vendor_status
        ))])

        models.on_subscription_updated(None, subscription, async=False)
        logger.info("customer %s expires, status %s -> %s",
                    subscription.customer, status, subscription.vendor_status)

    return result
