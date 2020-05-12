from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import View
from . import helpers

from sm.product.gsc import models
from sm.product.gsc.models import get_open_order_detail

from .decorator_view import profile_required

import logging

logger = logging.getLogger(__name__)

class LicenseAddView(View):
    def post(self, request, *args, **kwargs):
        customer = request.user.sm.customer
        if customer.reseller:
            return helpers.redirect_to_reseller(customer.reseller)

        subscription = models.SubscriptionManager(customer).get_subscription()
        if subscription.paid:
            product = subscription.product
            if product.version == models.ProductVersionEnum.BASIC:
                return redirect(reverse("gsc:pricing") + "?upgrade=true")
            order_detail = get_open_order_detail(customer)
            order = order_detail.order if order_detail else models.create_order(customer)
            catalog = subscription.catalog
            pk = order_detail.pk if order_detail else None
            logger.info("sanja: %d", pk)
            if product.tier_number < 0:
                tier = catalog.get_tier(-1, version=product.version, plan=product.plan)
                amount = max(1, subscription.billable_licenses - subscription.vendor_licenses)
                sub_total = amount * tier.price
            else:
                tier = catalog.get_tier(product.tier_number + 1, version=product.version, plan=product.plan)
                amount = product.tier_number
                sub_total = tier.price

            models.OrderDetail.objects.update_or_create(
                {
                    'order': order,
                    'product': tier.product,
                    'catalog': catalog,
                    'subscription': subscription,
                    'unit_price': tier.price,
                    'amount': amount,
                    'sub_total': sub_total
                }, pk=pk
            )

            return redirect(reverse("gsc:checkout"))
        return redirect(reverse("gsc:subscriptions"))


@profile_required
def license_add(request):
    return LicenseAddView.as_view()(request)
