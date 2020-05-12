from __future__ import absolute_import
from . import models
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from sm.product.gsc import zoho
from sm.product.gsc import failed_transaction_manager

import logging

logger = logging.getLogger(__name__)


def on_order_paid(order_detail, expiry_date, payment_gateway="Braintree GAE", checkout_type='first', payment_id=''):
    """

    :param checkout_type: checkout type
    :param payment_gateway: payment gateway (see models.Subscription.payment_gateway)
    :type order_detail: models.OrderDetail
    :type expiry_date: datetime.datetime.Datetime
    """

    order = order_detail.order
    subscription = order_detail.subscription
    subscription.next_invoice_date = expiry_date + relativedelta(days=7)
    subscription.expiry_date = expiry_date
    subscription.product = order_detail.product
    subscription.vendor_status = models.VendorStatus.PAID.value
    subscription.vendor_licenses = order_detail.amount
    subscription.renewal_option = models.RenewalOption.RENEW
    subscription.plan = order_detail.product.plan
    subscription.order = order
    subscription.payment_gateway = payment_gateway
    subscription.save()
    order.status = models.OrderStatus.PAID
    order.date = timezone.now()
    order.save()

    # clear outcome
    subscription.customer.set_last_payment_status(
        outcome="IPN Success" if payment_gateway == 'Paypal GSC' else "Braintree Success",
        payment_id=(
            "paypal:%s" if payment_gateway == 'Paypal GSC' else "braintree:%s"
        ) % payment_id
    )
    subscription.customer.save()

    if subscription.customer.payment_position == 1:
        zoho.update_potential(order_detail, checkout_type="new")
        subscription.customer.last_payment_type = 'new'
        logger.info("subscription %s is created. new expiry date: %s", subscription, subscription.expiry_date)
    else:
        potential_id = failed_transaction_manager.find_potential_id(order_detail.order)
        zoho.create_potential(order_detail, checkout_type, potential_id=potential_id)
        subscription.customer.last_payment_type = checkout_type
        logger.info("subscription %s is updated. new expiry date: %s", subscription, subscription.expiry_date)

    subscription.customer.save()
    models.on_subscription_updated(None, subscription, force=True)
    return order_detail

