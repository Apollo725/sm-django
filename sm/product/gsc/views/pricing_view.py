import logging

from bunch import Bunch
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.shortcuts import resolve_url
from django.template import RequestContext

from sm.product.gsc import forms
from sm.product.gsc import models
from sm.product.gsc import zoho
from sm.product.gsc.views import helpers
from .decorator_view import profile_required


logger = logging.getLogger(__name__)


def pricing_post(request, upgrade=False):
    customer = request.user.sm.customer
    form = forms.OrderRequestForm(request.POST)
    profile = models.get_vendor_profile(customer)
    subscription = models.SubscriptionManager(customer).get_subscription()

    if form.is_valid():
        # reuse not completed order
        order_detail = models.get_open_order_detail(customer)

        if order_detail:
            catalog = order_detail.catalog
        else:
            catalog = subscription.catalog or models.get_default_catalog()

        data = Bunch(form.cleaned_data)

        logger.debug("order request: %s, %s", customer, data.toDict())
        tier = catalog.get_tier(data.amount,
                                version=data.version,
                                plan=data.plan
                                )
        if not order_detail:
            order = models.create_order(customer)
        else:
            order = order_detail.order

        pk = None if not order_detail else order_detail.pk

        if tier.per_user:
            amount = max(5, profile.users, subscription.vendor_licenses)  # use number of users in profile
            price = tier.price * amount
        else:
            amount = data.amount
            price = tier.price

        models.OrderDetail.objects.update_or_create(
            dict(order=order,
                 product=tier.product,
                 catalog=catalog,
                 subscription=subscription,
                 sub_total=price,
                 amount=amount),
            pk=pk
        )

        logger.info("Order is created by %s", customer.name)
        return redirect(resolve_url("gsc:checkout") + ("?upgrade=true" if upgrade else ""))


@profile_required
def pricing(request):
    upgrade = request.GET.get('upgrade') == 'true'
    customer = request.user.sm.customer
    if customer.reseller and upgrade:
        return helpers.redirect_to_reseller(customer.reseller)

    profile = models.get_vendor_profile(customer)

    subscription = models.SubscriptionManager(customer).get_subscription()
    upgrade = upgrade and subscription.product.version != models.ProductVersionEnum.ENTERPRISE and (
        subscription.paid)
    if subscription.paid and not upgrade:
        return redirect(reverse("gsc:subscriptions"))

    if request.method == 'POST':
        response = pricing_post(request, upgrade)
        if response:
            return response

    if subscription:
        catalog = subscription.catalog
    else:
        catalog = models.Catalog.objects.filter(
            default=True
        ).first()
        if not catalog:
            raise models.Catalog.DoesNotExist("Can't find default price catalog")

    amount = -1

    tiers = dict(
        yearly=dict(
            pro=catalog.get_tier(
                amount,
                version=models.ProductVersionEnum.PRO,
                plan=models.SubscriptionPlan.ANNUAL_YEARLY),
            enterprise=catalog.get_tier(
                amount,
                version=models.ProductVersionEnum.ENTERPRISE,
                plan=models.SubscriptionPlan.ANNUAL_YEARLY),
            basic=catalog.get_tier(
                5, version=models.ProductVersionEnum.BASIC,
                plan=models.SubscriptionPlan.ANNUAL_YEARLY
            )
        ),
        monthly=dict(
            pro=catalog.get_tier(
                amount,
                version=models.ProductVersionEnum.PRO,
                plan=models.SubscriptionPlan.FLEX_PREPAID),
            enterprise=catalog.get_tier(
                amount,
                version=models.ProductVersionEnum.ENTERPRISE,
                plan=models.SubscriptionPlan.FLEX_PREPAID),
            basic=catalog.get_tier(
                5, version=models.ProductVersionEnum.BASIC,
                plan=models.SubscriptionPlan.FLEX_PREPAID
            )
        )
    )

    if request.method == 'GET':
        zoho.price_viewed(request.user.sm)

    order_detail = models.get_open_order_detail(customer)
    if subscription.paid:
        plan = subscription.product.plan
    elif order_detail:
        plan = order_detail.product.plan
    else:
        plan = models.SubscriptionPlan.ANNUAL_YEARLY

    inactive_products = {'basic': False, 'enterprise': False}
    if upgrade:
        inactive_products['basic'] = True
        inactive_products['enterprise'] = subscription.product.version > models.ProductVersionEnum.PRO

        logger.debug("inactive products: %s", inactive_products)

    return render(
        request,
        template_name="sm/product/gsc/pricing.html",
        context_instance=RequestContext(
            request,
            {
                'tiers': tiers,
                'profile': profile,
                'plan': plan,
                'subscription': subscription,
                'versions': models.ProductVersion,
                'inactive_products': inactive_products,
                'upgrade': request.GET.get('upgrade')
            },
            processors=[context_processor]
        )
    )


def context_processor(request):
    return {
        "PRODUCT_URL": settings.GSC_PRODUCT_URL,
        "absolute_url": request.build_absolute_uri()
    }
