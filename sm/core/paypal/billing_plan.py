from __future__ import absolute_import

import logging

import braintree
import braintree.exceptions
import paypalrestsdk
import paypalrestsdk.exceptions
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from sm.core import models
from sm.core.paypal.api import api, PAYPAL_API_DATE_FORMAT

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


def dump_errors(result):
    if result.errors:
        return "; ".join(
            [error.message for error in result.errors.deep_errors]
        )
    else:
        return result.message


def get_customer(sm_user):
    customer = models.BraintreeCustomer.objects.filter(
        user=sm_user
    ).first()

    if customer:
        return customer.bt_id


def update_customer(sm_user):
    customer_id = 'sm_' + sm_user.auth_user.username
    names = sm_user.name.split(" ")

    params = dict(
        email=sm_user.contact_email or sm_user.email,
        first_name=names[0].strip(),
        last_name=names[-1].strip(),
        phone=sm_user.phone_number
    )

    try:
        customer_id = braintree.Customer.find(customer_id).id
        result = braintree.Customer.update(customer_id, params)
        if result.is_success:
            customer_id = result.customer.id
        else:
            logger.error("Failed to update customer %s", dump_errors(result))
            return

    except braintree.exceptions.not_found_error.NotFoundError:
        params['id'] = customer_id
        result = braintree.Customer.create(params)

        if result.is_success:
            customer_id = result.customer.id
        else:
            logger.error("Failed to create customer %s", dump_errors(result))
            return

    models.BraintreeCustomer.objects.update_or_create(
        dict(
            user=sm_user,
            bt_id=customer_id
        ), user=sm_user
    )

    return customer_id


def create_if_not_exists(product_catalog):
    """
    :param return_url: the return url
    :type product_catalog: sm.core.models.ProductCatalog
    """
    # TODO: (sanja) when we start using new plans, make sure this code doesn't raise error
    if product_catalog.product.plan not in [models.SubscriptionPlan.FLEX_PREPAID,
                                            models.SubscriptionPlan.ANNUAL_YEARLY]:
        raise ValueError("Only flex prepaid and yearly paid is supported")

    monthly = product_catalog.product.plan == models.SubscriptionPlan.FLEX_PREPAID

    plan = models.PaypalBillingPlan.objects.filter(
        product_catalog=product_catalog,
    ).first()

    amount = dict(
        value=float(product_catalog.price),
        currency='USD'
    )

    if not plan:
        plan = paypalrestsdk.BillingPlan(dict(
            name=str(product_catalog),
            description=str(product_catalog),
            type='INFINITE',
            payment_definitions=[dict(
                name='Regular Payments',
                type='REGULAR',
                frequency_interval="1",
                frequency='MONTH' if monthly else "YEAR",
                amount=amount,
                cycles=0
            )],
            merchant_preferences=dict(
                return_url="http://localhost",
                cancel_url="http://localhost",
                initial_fail_amount_action='CANCEL',
                max_fail_attempts=1
            )
        ), api)

        if plan.create():
            if plan.activate():
                plan = models.PaypalBillingPlan.objects.create(
                    product_catalog=product_catalog,
                    paypal_id=plan.id
                )
            else:
                raise Error(plan.error)
        else:
            raise Error(plan.error)

    return plan


def create_billing_agreement(name, plan_id, return_url, cancel_url, notify_url=None):
    start_date = timezone.now() + relativedelta(seconds=10)

    override_merchant_preferences = dict(
        cancel_url=cancel_url,
        return_url=return_url
    )

    if notify_url:
        override_merchant_preferences['notify_url'] = notify_url

    agreement = paypalrestsdk.BillingAgreement(dict(
        name=name,
        description=name,
        start_date=start_date.strftime(PAYPAL_API_DATE_FORMAT),
        plan=dict(
            id=plan_id
        ),
        payer=dict(
            payment_method='paypal'
        ),
        override_merchant_preferences=dict(
            cancel_url=cancel_url,
            return_url=return_url
        )
    ), api)

    if not agreement.create():
        raise Error(agreement.error)

    return agreement


def find_approval_link(agreement):
    for link in agreement.links:
        if link.rel == 'approval_url':
            return link.href


def execute_agreement(token):
    return paypalrestsdk.BillingAgreement.execute(token, api=api)


def get_transactions(agreement_id, start=None, end=None):
    date_format = '%Y-%m-%d'
    if start is None:
        start = timezone.now() + relativedelta(days=-1)
    if end is None:
        end = timezone.now()

    transactions = paypalrestsdk.BillingAgreement(dict(
        id=agreement_id
    ), api=api).search_transactions(
        start_date=start.strftime(date_format),
        end_date=end.strftime(date_format),
        api=api
    )

    if not transactions.success():
        raise Error(transactions.error)
    else:
        return transactions.agreement_transaction_list


def get_completed_transactions(agreement_id, retries=5, start=None, end=None):
    max_retries = retries

    def _get_completed_transactions(agreement_id, retries, start=None, end=None):
        if retries > 0:
            logger.debug("Trying to get completed transaction for %s", agreement_id)
            import time
            time.sleep(2 ** (max_retries - retries))
            retries -= 1

            transactions = get_transactions(agreement_id, start, end)
            for txn in transactions:
                if txn.status == 'Completed':
                    return txn

            return _get_completed_transactions(
                agreement_id,
                retries=retries,
                start=start, end=end)
        return None

    return _get_completed_transactions(agreement_id, retries, start, end)
