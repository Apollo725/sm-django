from __future__ import absolute_import

from django.dispatch import Signal

subscription_updated = Signal(providing_args=['instance'])
customer_updated_by_admin = Signal(providing_args=['instance'])
