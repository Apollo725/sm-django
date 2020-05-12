from __future__ import absolute_import

import braintree

from . import models
from sm.core.paypal import billing_plan
import logging
from sm.core.braintree_helper import save_payment_detail

logger = logging.getLogger(__name__)


def create_payment_method(customer_id, profile, name, payment_method_nonce, customer_name=None):
    """Create payment method with payment method nonce

    :param customer_id:  The id of customer
    :type customer_id: string
    :param profile: The profile of customer, could be None
    :type profile: models.Profile
    :param user: The user
    :type user: models.User
    :param payment_method_nonce: payment nonce
    :type payment_method_nonce: string
    :param customer_name the domain name of the parameter used for better logs
    :type customer_name: string
    :return: None if failed, a payment method created
    """
    names = name.split(" ")
    billing_address = dict(
        first_name=names[0].strip(),
        last_name=names[-1].strip(),
    )

    if profile:
        country = models.Country.objects.filter(name=profile.country).first()
        if country is not None:
            country_code = country.code
        else:
            country_code = "US"

        billing_address.update(dict(
            country_code_alpha2=country_code,
            postal_code=profile.zip_code,
            locality=profile.city,
            street_address=profile.address,
            region=profile.state
        ))

    result = braintree.PaymentMethod.create(dict(
        customer_id=customer_id,
        payment_method_nonce=payment_method_nonce,
        billing_address=billing_address
    ))

    if customer_name is None:
        customer_name = name
    if result.is_success:
        models.save_payment_method(customer_id, result.payment_method.token)
        save_payment_detail(result.payment_method)
        logger.info("Success to create payment method for %s, token: %s", customer_name,
                    result.payment_method.token)
        return result.payment_method
    else:
        logger.error("Failed to create payment method for %s, error: %s", customer_name,
                     billing_plan.dump_errors(result))
        logger.debug(result)
        return None


def charge_order(payment_total, payment_method, order_id, user=None):
    """Charge customer with payment method

    :param user: The user who is charged
    :type user: string
    :param payment_total: The total amount to sale like 25.50
    :type payment_total: float
    :param payment_method: The payment method
    :type payment_method: braintree.PaymentMethod
    :return:
    """

    result = braintree.Transaction.sale(
        dict(
            amount=str(float(payment_total)),
            payment_method_token=payment_method.token,
            options=dict(
                submit_for_settlement=True
            ),
            order_id=str(order_id)
        )
    )

    if not result.is_success:
        logger.warn("Failed to charge user %s %s", user,
                     billing_plan.dump_errors(result))
    else:
        logger.info("Succeed to charge user %s, order_id %s, amount %s", user, order_id, payment_total)

    return result
