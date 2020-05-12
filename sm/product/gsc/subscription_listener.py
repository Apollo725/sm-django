from __future__ import absolute_import

import dateutil.parser
import pytz

from sm.product.gsc.models import *
from . import subscription_manager
from . import order_manager
from . import zoho
from . import failed_transaction_manager

tz = pytz.timezone('America/Los_Angeles')


def parse_date(date_str):
    return tz.localize(dateutil.parser.parse(date_str, ignoretz=True))


def on_subscription_cancel(sender, profile_id, **kwargs):
    logger.info("Subscription %s is cancelled", profile_id)
    transaction = PaypalTransaction.objects.filter(profile_id=profile_id).order_by("-payment_time").first()
    if transaction:
        subscription = Subscription.objects.filter(order=transaction.order).first()
        if subscription:
            assert isinstance(subscription, Subscription)
            if not subscription.payment_gateway or subscription.payment_gateway == 'Paypal GSC':
                subscription.renewal_option = RenewalOption.CANCEL
                subscription.save()
                logger.info("Subscription %s is cancelled", subscription)
                on_subscription_updated(None, subscription, force=True)


def on_subscription_failed(sender, profile_id, params, **kwargs):
    logger.info("Subscription %s is cancelled", profile_id)
    transaction = PaypalTransaction.objects.filter(profile_id=profile_id).order_by("-payment_time").first()

    if transaction:
        subscription = Subscription.objects.filter(order=transaction.order).first()
        if subscription:
            assert isinstance(subscription, Subscription)
            if not subscription.payment_gateway or subscription.payment_gateway == 'Paypal GSC':
                order = order_manager.create_renewal_order(subscription)

                failed_transaction = failed_transaction_manager.create(
                    order, params.get('txn_type')
                )

                zoho.update_failed_potential(
                    order_detail=order.details.first(),
                    failed_transaction=failed_transaction,
                    checkout_type="renewal"
                )

                customer = subscription.customer
                customer.set_last_payment_status(
                    outcome=params.get('txn_type'),
                    payment_id="paypal:%s_%s" % (
                        profile_id,
                        params.get('txn_id', '')
                    )
                )
                customer.last_payment_type = 'renewal'
                customer.save()
                zoho.update_account(customer)


def on_subscription_payment(sender, profile_id, txn_id, params, **kwargs):
    logger.info("Subscription %s is paid", profile_id)
    transaction = PaypalTransaction.objects.filter(profile_id=profile_id).order_by("-payment_time").first()
    if transaction:
        if PaypalTransaction.objects.filter(txn_id=txn_id).exists():
            logger.warn("Transaction has existed %s", txn_id)
            return

        assert isinstance(transaction, PaypalTransaction)
        order = transaction.order
        subscription = order.details.first().subscription

        order = order_manager.create_renewal_order(subscription)
        PaypalTransaction.objects.create(
            order=order,
            profile_id=profile_id,
            txn_id=txn_id,
            payment_time=parse_date(
                params['payment_date']
            )
        )
        order_detail = order.details.first()

        logger.info("Going to update subscription %s, paypal subscription is renewed: %s", subscription, profile_id)
        if 'next_payment_date' in params:
            expiry_date = parse_date(params['next_payment_date'])
        else:
            expiry_date = calculate_expiration_date(
                start_date=parse_date(params['payment_date']),
                monthly=order_detail.product.monthly)

        order_detail = subscription_manager.on_order_paid(
            order_detail,
            expiry_date,
            payment_gateway="Paypal GSC",
            checkout_type="renewal",
            payment_id="%s_%s" % (profile_id, txn_id)
        )

        subscription = order_detail.subscription

        if 'subscr_date' in params:
            subscription.start_plan_date = parse_date(params['subscr_date'])
        subscription.plan = order_detail.product.plan
        subscription.save()
    else:
        logger.warn("Can't find profile with id: %s", profile_id)
        from django.core.mail import send_mail
        import urllib
        send_mail(
            "Can't find profile with id: %s in sm, the domain wasn't migrated probably." % profile_id,
            "", from_email=settings.EMAIL_HOST_USER, recipient_list=settings.CANCEL_PAYPAL_PROFILE_RECEIVER.split(","), html_message="""
            <a href="{link}">{link}</a>
            <p>Find the domain name in the ipn message detail</p>
            <p>detail:</p>
            <pre>{ipn}</pre>
            """.format(
                link="https://www.paypal.com/webscr?cmd=_profile-recurring-payments&encrypted_profile_id=%s" % profile_id,
                ipn=urllib.urlencode(params)
            )
        )
