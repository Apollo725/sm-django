import logging

from sm.core.models import Country, Catalog
from sm.core.predefined_constants import EUR_CATALOG_NAME, CAD_CATALOG_NAME, \
    RESELLER_CANADA, RESELLER_FRANCE, RESELLER_WORLD

logger = logging.getLogger(__name__)


def get_customer_catalog(customer, currency=None):
    if not currency:
        currency = Country.objects.get(code=customer.vendor_profile_set.get().country).currency
    if currency.encode('utf-8') == 'EUR'.encode('utf-8'):
        try:
            return Catalog.objects.get(name=EUR_CATALOG_NAME)
        except:
            logger.warn("Cannot find catalog with name: {}".format(EUR_CATALOG_NAME))
    elif currency.encode('utf-8') == 'CAD'.encode('utf-8'):
        try:
            return Catalog.objects.get(name=CAD_CATALOG_NAME)
        except:
            logger.warn("Cannot find catalog with name: {}".format(CAD_CATALOG_NAME))
    return Catalog.objects.get(default=True)


def get_customer_currency(customer):
    return Country.objects.get(code=customer.vendor_profile_set.get().country).currency


def get_vendor_console(customer):
    country = Country.objects.get(code=customer.vendor_profile_set.get().country)
    if country.name == 'Canada':
        return RESELLER_CANADA
    elif country.continent == 'Europe':
        return RESELLER_FRANCE
    else:
        return RESELLER_WORLD


def get_customer_region(customer):
    country = Country.objects.get(code=customer.vendor_profile_set.get().country)
    if country.name == 'Canada':
        return 'Canada'
    elif country.name == 'France':
        return 'France'
    elif country.continent == 'Europe':
        return 'Europe'
    else:
        return None


def check_google_reseller_console(subscription, customer):
    """This function checks which reseller console should be used base on the Policy table,
    and base on the following document:
    https://docs.google.com/document/d/1xGZmSBYfwzpM_4Td4AXel05dmRbZdyvmtVT7eqa6cTk/edit#heading=h.n7pfkejnob3q"""

    # region = _get_customer_region(customer)
    # if region:
    #     Policy.objects.get(product_category='Google', customer_type=customer.type,
    #                        customer_region=region)
    # else:
    #     Policy.objects.get(product_category='Google', customer_type=customer.type,
    #                        customer_region='')

    subscription['currency'] = get_customer_currency(customer)
    subscription['vendor_console'] = get_vendor_console(customer)
    subscription['region'] = get_customer_region(customer)
    subscription['catalog'] = get_customer_catalog(customer)
    return subscription


def check_policy(subsriptions):
    pass
