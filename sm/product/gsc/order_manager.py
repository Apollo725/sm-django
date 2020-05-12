from __future__ import absolute_import
from . import models


def create_renewal_order(subscription):
    """Create a renewal order

    :type subscription: models.Subscription
    :return:
    """
    product_catalog = models.ProductCatalog.objects.get(
        catalog=subscription.catalog,
        product=subscription.product
    )

    if subscription.product.tier_number < 0:  # per user price
        sub_total = product_catalog.price * subscription.vendor_licenses
        amount = subscription.vendor_licenses
    else:
        sub_total = product_catalog.price
        amount = subscription.product.tier_number

    order_detail = models.OrderDetail.objects.filter(
        order__due_date=subscription.expiry_date,
        product=subscription.product,
        catalog=subscription.catalog,
        sub_total=sub_total,
        amount=amount,
        order__status=models.OrderStatus.RENEWING,
        subscription=subscription
    ).order_by("-id").first()

    if not order_detail:
        order = models.Order.objects.create(
            customer=subscription.customer,
            name="GSC renewal order for %s" % subscription.customer.name,
            currency=subscription.customer.currency,
            status=models.OrderStatus.RENEWING,
            due_date=subscription.expiry_date
        )

        models.OrderDetail.objects.create(
            order=order,
            product=subscription.product,
            catalog=subscription.catalog,
            subscription=subscription,
            sub_total=sub_total,
            amount=amount
        )
    else:
        order = order_detail.order
    return order
