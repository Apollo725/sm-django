from __future__ import absolute_import

import braintree
import braintree.credit_card
import braintree.paypal_account
import braintree.exceptions
from django.utils import timezone

from sm.core.paypal.billing_plan import dump_errors
from . import models
import logging

logger = logging.getLogger(__name__)


def search_payment_method(customer):
    payment_methods = []
    customer_id_list = ['sm_' + user.auth_user.username for user in customer.users.all()]
    for customer_id in customer_id_list:
        user = models.User.objects.get(auth_user__username=customer_id[3:])
        try:
            customer = braintree.Customer.find(customer_id)
            for payment_method in customer.payment_methods:
                payment_methods.append([payment_method, user, customer_id])
                logger.info("Find a payment method for %s: %s", user, payment_method)

        except braintree.exceptions.NotFoundError:
            logger.info("No customer found in braintree for %s" % user)

    return payment_methods


def sync_payment_method(customer):
    methods = search_payment_method(customer)
    for method, user, customer_id in methods:
        if not models.BraintreePaymentMethod.objects.filter(token=method.token).exists():
            models.BraintreePaymentMethod.objects.create(
                customer_id=customer_id,
                token=method.token,
                default=method.default
            )
            logger.info("Payment method %s is saved for %s to sm", method.token, user)


def sync_all_payment_method():
    for customer in braintree.Customer.search([braintree.CustomerSearch.created_at <= timezone.now()]).items:
        user = models.User.objects.filter(auth_user__username=customer.id[3:]).first()
        if user:
            for method in customer.payment_methods:
                logger.info("Find a payment method for %s: %s", user, method)
                if not models.BraintreePaymentMethod.objects.filter(token=method.token).exists():
                    models.BraintreePaymentMethod.objects.create(
                        customer_id=customer.id,
                        token=method.token,
                        default=method.default
                    )
                    logger.info("Payment method %s is saved for %s to sm", method.token, user)

        else:
            logger.warn("Can't find user %s in sm " % customer.id[3:])


def cancel_all_subscriptions():
    for subscription in braintree.Subscription.search(
            [braintree.SubscriptionSearch.status == braintree.Subscription.Status.Active]
    ):
        result = braintree.Subscription.cancel(subscription.id)
        if result.is_success:
            models.BraintreeSubscription.objects.filter(bt_id=subscription.id).update(
                cancelled=True,
                status=result.subscription.status
            )
            logger.info("Cancel subscription %s successfully", subscription.id)
        else:
            logger.warn("Failed to cancel subscription %s: %s", subscription.id, dump_errors(result))


def sync_braintree_transaction():
    import pytz
    for instance in models.BraintreeSubscription.objects.all():
        if instance == instance.subscription.bt.order_by("-created_at").first():
            bt_subscription = braintree.Subscription.find(instance.bt_id)
            for transaction in bt_subscription.transactions:
                if transaction.status == braintree.Transaction.Status.Settled and transaction.type == 'sale':
                    logger.info("Braintree transaction is created for %s, completed_at: %s, id: %s, \n%s",
                                instance.subscription, transaction.created_at, transaction.id, transaction)

                    if not models.BraintreeTransaction.objects.filter(
                            order=instance.subscription.order).exists():
                        models.BraintreeTransaction.objects.update_or_create(dict(
                            order=instance.subscription.order,
                            status="Completed",
                            completed_date=transaction.created_at.replace(tzinfo=pytz.utc),
                            bt_id=transaction.id), bt_id=transaction.id
                        )
                    else:
                        logger.warn("order has been existed for %s", instance.subscription)
                    break
            else:
                logger.warn("No braintree transaction found for %s", instance.subscription)


def save_payment_detail(payment_method):
    try:
        bpm = models.BraintreePaymentMethod.objects.get(token=payment_method.token)
        bpm.default = payment_method.default
        if isinstance(payment_method, braintree.credit_card.CreditCard):
            bpm.type = 'credit_card'
            bpm.last_4_digits = payment_method.last_4
            bpm.card_type = payment_method.card_type
            bpm.expiration_date = payment_method.expiration_date
            bpm.save()
        elif isinstance(payment_method, braintree.paypal_account.PayPalAccount):
            bpm.type = 'paypal'
            bpm.email_address = payment_method.email
            bpm.save()

    except models.BraintreePaymentMethod.DoesNotExist:
        logging.error("No token found in BraintreePaymentMethod")


def get_payment_detail(token):
    return braintree.PaymentMethod.find(token)
