from datetime import datetime
from django.utils import timezone


def format_date(epoch):
    """This function takes epoch send from google and returns it as a datetime object"""
    dt = datetime.utcfromtimestamp(int(epoch) / 1000.0)
    tz_aware = timezone.make_aware(dt, timezone.utc)
    return tz_aware


def find_vendors(sub_list):
    """:arg sub_list: A list of subscriptions
       This function iterates over the subscriptions
       and creates a set with all the vendor names.
       :returns set of vendor names"""
    return set([sub.product.category.vendor.name for sub in sub_list])


def find_categories(sub_list):
    """:arg sub_list: A list of subscriptions
           This function iterates over the subscriptions
           and creates a set with all the product category names.
           :returns set of vendor names"""
    return set([sub.product.category.name for sub in sub_list])


def make_order_name(vendors, user):
    """:arg vendors: iterable of vendor names.
       :arg user: a User object
       This function creates a string with vendor names and the user.
       :returns str()"""
    return "{vendors} order for {user}".format(vendors='/'.join(vendors), user=user)


def flatten_dict(d):
    """Function to flatten dictionary, Taken from:
    https://codereview.stackexchange.com/questions/21033/flatten-dictionary-in-python-functional-style
    Important note: This function is recursive."""
    def expand(key, value):
        if isinstance(value, dict):
            return [(key + '.' + k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)
