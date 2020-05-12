from __future__ import absolute_import

import requests
from django.conf import settings
from django.dispatch import Signal
import logging
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def verify(body):
    if settings.PAYPAL_IPN_SANDBOX:
        url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
    else:
        url = 'https://www.paypal.com/cgi-bin/webscr'

    resp = requests.post(url + "?cmd=_notify-validate", body)
    return resp.content


def handle(body, params):
    ret = verify(body)
    if ret != "VERIFIED":
        logger.error("Failed to verify ipn message (%s): %s", ret, params)
        send_mail(
            "Failed to verify ipn message",
            body,
            settings.EMAIL_HOST_USER,
            settings.ERROR_RECEIVER.split(",")
        )
    else:
        if not params.get('receiver_email', '').lower() == settings.PAYPAL_IPN_RECEIVER.lower():
            logger.warn("Error ipn message: bad receiver_email %s, %s", params.get('receiver_email', ''), params)
            return

        handle_subscription(params)


def handle_subscription(params):
    sender = 'paypal'
    txn_type = params.get('txn_type', None)
    if txn_type == 'subscr_payment' and 'Completed' == params.get('payment_status'):
        subscription_payment.send(sender,
                                  profile_id=params.get('subscr_id'),
                                  txn_id=params.get('txn_id'), params=params)
    elif txn_type == 'recurring_payment' and 'Completed' == params.get('payment_status'):
        subscription_payment.send(sender,
                                  profile_id=params.get('recurring_payment_id'),
                                  txn_id=params.get('txn_id'), params=params)
    elif txn_type == 'subscr_cancel':
        subscription_cancel.send(sender,
                                 profile_id=params.get('subscr_id'), params=params)
    elif txn_type == 'recurring_payment_profile_cancel':
        subscription_cancel.send(sender,
                                 profile_id=params.get('recurring_payment_id'), params=params)
    elif txn_type in ['subscr_failed', 'recurring_payment_failed']:
        subscription_failed.send(sender,
                                 profile_id=params.get('subscr_id', params.get('recurring_payment_id')),
                                 params=params)
    else:
        return params


subscription_payment = Signal(providing_args=(
    'profile_id', 'txn_id', 'params'
))

subscription_cancel = Signal(providing_args=(
    'profile_id', 'params'
))

subscription_failed = Signal(providing_args=(
    'profile_id', 'params'
))
