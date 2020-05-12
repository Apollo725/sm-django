from django.utils import timezone

from sm.core.models import (DisplayProduct, OrderType, Product,
                            SubscriptionStatus)


def create_display_products_from_product(product):
    display_products = DisplayProduct.objects.filter(current_product=product)
    if display_products.count() < (Product.objects.count() * len(OrderType)):
        for action_type in OrderType:
            displayed_products = product.category.products.exclude(
                    id__in=DisplayProduct.objects.filter(
                        current_product=product,
                        type=action_type
                    ).values_list('displayed_product', flat=True)
                )
            for displayed_product in displayed_products:
                DisplayProduct.objects.create(
                    current_product=product,
                    displayed_product=displayed_product,
                    type=action_type,
                    enabled=True,
                    highlighted=False,
                    showcase_alternate=True,
                    show_small=True,
                )


def get_user_subscriptions(customer):
    '''
    Returns the most recent and active user subscriptions.
    '''
    return customer.subscription_set \
        .order_by('-created_at') \
        .filter(
            expiry_date__gte=timezone.now(),
            status=SubscriptionStatus.ACTIVE
        )
