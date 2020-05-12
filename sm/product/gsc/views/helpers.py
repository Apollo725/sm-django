from django.conf import settings
from sm.product.gsc import models
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def extend_context(kwargs):
    kwargs.setdefault("PRODUCT_URL", settings.GSC_PRODUCT_URL)
    return kwargs


def show_pricing_menu(request):
    customer = request.user.sm.customer
    subscription = models.SubscriptionManager(customer).get_subscription()
    return not subscription.paid


def redirect_to_reseller(reseller):
    return redirect(get_reseller_link(reseller))


def get_reseller_link(reseller):
    return reverse('frontend:reseller-page', kwargs={'reseller_name': reseller.verbose_name})
