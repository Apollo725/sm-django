from django.contrib.staticfiles.templatetags.staticfiles import static
from rest_framework.exceptions import ValidationError

from sm.core.models import ProductCatalog, BraintreePaymentMethod, Subscription, \
    Product, ProductCategory, Customer, SubscriptionStatus
from sm.core.predefined_constants import GSUITE_PRODUCT_CATEGORY_CODE


# TODO: this should not be hardcoded. The images should be in the database
def product_image_url(obj):
    """This function returns static urls of specific product"""
    if not obj.category or not obj.category.code:
        return
    if obj.category.code == 'GDRIVE':
        return static('sm/new_frontend/img/drive.png')
    if obj.category.code == 'GVAULT':
        return static('sm/new_frontend/img/vault.png')
    if obj.category.code == 'GSUITE':
        return static('sm/new_frontend/img/g_suite.png')
    if obj.category.code == 'GSC':
        return static('sm/new_frontend/img/GAE.png')
    if obj.category.code == 'GSC_GMAIL':
        return static('sm/new_frontend/img/gsc_gmail.png')


def catalog_per_user(obj):
    """This function returns per_user value for catalog"""
    return ProductCatalog.objects.get(product=obj.product, catalog=obj.catalog).per_user


def catalog_unit(obj):
    """This function returns unit value for catalog which is required for parent subscription json"""
    if catalog_per_user(obj):
        return "user"
    else:
        return "pack"


def get_payment_method(methods):
    """This function returns payment method of current customer"""
    payment_method = None
    for method, _, _ in methods:
        payment_method = BraintreePaymentMethod.objects.filter(token=method.token).first()
    return payment_method


def get_subscription_by_product_or_product_category(param):
    """This function returns Subscription filtered by customer and vendor_sku"""
    customer = Customer.objects.filter(name=param['domain'])
    subscription = Subscription.objects.filter(customer=customer, product__vendor_sku=param['vendor_sku'])
    if subscription.exists() and param['vendor_sku'] is not None:
        return subscription.first()
    else:
        return None


def get_subscription_by_product_category(params, category=None):
    """Returns Subscription filtered by customer and product.category"""
    customer = Customer.objects.filter(name=params['domain'])
    if not category:
        category = ProductCategory.objects.filter(code=GSUITE_PRODUCT_CATEGORY_CODE)
    subscription = Subscription.objects.filter(customer=customer, product__category=category)
    if subscription.exists():
        return subscription.first()
    else:
        return None


def category_detect(param):
    """This function delete GSUITE Subscription if provided vendor_sku is for GSUITE product"""
    customer = Customer.objects.filter(name=param['domain'])
    product = Product.objects.filter(vendor_sku=param['vendor_sku'])
    if product.exists():
        category = product.first().category
    else:
        raise ValidationError('product does not exist for %s' % param['vendor_sku'])
    if category is not None and category.code == GSUITE_PRODUCT_CATEGORY_CODE:
        subscription = Subscription.objects.filter(customer=customer, product__category=category)
        if subscription.exists():
            subscription.delete()


def remove_subscription(response):
    """This function will remove subscription which is not mentioned in request"""
    customers = set(map(lambda x: dict(x)['domain'], response.data))
    for customer in customers:
        ids = [dict(data)['id'] for data in response.data if dict(data)['domain'] == customer]
        customer = Customer.objects.filter(name=customer)
        subscriptions = Subscription.objects.filter(
            customer=customer,
            status=SubscriptionStatus.DETECTED.value
            ).exclude(id__in=ids)
        if subscriptions.exists():
            subscriptions.delete()
