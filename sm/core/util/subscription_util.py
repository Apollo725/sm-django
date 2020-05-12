from ..models import SubscriptionPlan


def get_billing_period(subscription):
    """

    :param subscription:
    :return: a string representing the billing period
        options: year/month
    """
    plan = subscription.plan
    if not plan:
        return None
    if plan in (SubscriptionPlan.FLEX_PREPAID, SubscriptionPlan.ANNUAL_MONTHLY):
        return "month"
    else:
        return "year"
