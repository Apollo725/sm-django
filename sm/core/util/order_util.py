from dateutil.relativedelta import relativedelta

from .. import models
from subscription_util import get_billing_period


def get_valid_from(order):
    return order.due_date


def get_valid_to(order):
    valid_from = order.due_date
    if valid_from:
        if _is_for_full_billing_period(order.name):
            order_detail = order.details.first()
            if order_detail and hasattr(order_detail, 'subscription'):
                subscription = order.details.first().subscription
                #TODO consider to replace with
                #request_customer = order.customer
                #subscription = models.SubscriptionManager(request_customer).get_subscription()
                return add_billing_period(valid_from, get_billing_period(subscription))
        else:
            previous_order = models.Order.objects.filter(customer=order.customer,
                                                         status=models.OrderStatus.PAID,
                                                         date__lt=order.date).order_by('-date').first()
            return get_valid_to(previous_order)
    return None


def add_billing_period(date, period):
    if period == 'year':
        return date + relativedelta(years=1)
    elif period == 'month':
        return date + relativedelta(months=1)
    return None


def _is_for_full_billing_period(name):
    if 'license' in name or 'upgrade' in name:
        return False
    return True


def is_monthly_plan(order_detail):
    return order_detail.product.plan == models.SubscriptionPlan.FLEX_PREPAID or \
           order_detail.product.plan == models.SubscriptionPlan.ANNUAL_MONTHLY
