from __future__ import absolute_import

from functools import wraps

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core import mail

import time
import traceback
import sys

executor = ThreadPoolExecutor(max_workers=10)


def async(func):
    """
    This decorator exists to prevent the server from sending too many requests to Zoho CRM
    """
    def inner(*args, **kwargs):
        if settings.TESTING:
            return func(*args, **kwargs)
        else:
            delay = kwargs.pop('delay', 0.5)
            if kwargs.pop('async', True):
                def new_func():
                    # noinspection PyBroadException
                    try:
                        time.sleep(delay)
                        func(*args, **kwargs)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        raise

                return executor.submit(new_func)
            else:
                return func(*args, **kwargs)

    return wraps(func)(inner)


@async
def cancel_paypal_profile(customer):
    from .models import PaypalTransaction

    paypal_transaction = PaypalTransaction.objects.filter(order__customer=customer).first()

    if paypal_transaction:
        assert isinstance(paypal_transaction, PaypalTransaction)
        if "fake" not in paypal_transaction.profile_id:
            send_mail_cancel_paypal_profile(customer, paypal_transaction.profile_id)


PROFILE_LINK = "https://www.paypal.com/us/cgi-bin/webscr?cmd=_profile-recurring-payments&encrypted_profile_id={profile_id}"


def send_mail_cancel_paypal_profile(customer, profile_id):
    mail.send_mail(
        "[SM Alert] Customer pays through braintree, make sure the paypal profile %s is cancelled for %s" % (
            profile_id, customer),
        """Hi Danielle,

Customer {domain} paid through braintree, please make sure the paypal profile is cancelled

Its subscription id is {profile_id}

Link: {link}""".format(
            domain=customer,
            profile_id=profile_id,
            link=PROFILE_LINK.format(profile_id=profile_id)),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email.strip() for email in settings.CANCEL_PAYPAL_PROFILE_RECEIVER.split(",")]
    )

