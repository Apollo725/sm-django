import re
from calendar import monthrange
from datetime import date, timedelta

from django.utils import timezone

from sm.core.models import (BillingCycleEnum,
                            FrequencyEnum, Order, OrderDetail, OrderDetailType,
                            OrderStatus, ProductCatalog,
                            ProductCategory,
                            SubscriptionOrderAddStrategy,
                            SubscriptionOrderUpgradeStrategy,
                            VendorProfile)

from .general_utils import find_categories, make_order_name
from .policy import get_customer_currency


def _timedelta_to_days(delta):
    return delta.total_seconds() / 86400.0


def _extract_currency_from_subscriptions(subscriptions):
    currency_set = {item.currency for item in subscriptions}
    currency = currency_set and currency_set.pop()
    if len(currency_set) != 0 or not currency:
        raise ValueError('All subscriptions is must have the same currency.')
    return currency


def _extract_invoiced_customer_from_subscriptions(subscriptions):
    invoiced_customer_set = {item.invoiced_customer for item in subscriptions}
    invoiced_customer = invoiced_customer_set and invoiced_customer_set.pop()
    if len(invoiced_customer_set) != 0 or invoiced_customer is None:
        raise ValueError(
            'All subscriptions is must have invoiced customer. And this '
            'invoiced customer must be the same in all subscriptions.'
        )


def create_orders_from_google_subscriptions(subscriptions, customer):
    currency = _extract_currency_from_subscriptions(subscriptions)
    invoiced_customer = _extract_invoiced_customer_from_subscriptions(subscriptions)
    order_name = make_order_name(find_categories(subscriptions), customer.name)

    order = create_order_instance(customer=invoiced_customer, name=order_name)
    order.currency = currency
    order.save()

    for subscription in subscriptions:
        detail = create_order_detail_instance(
            order=order,
            product=subscription.product,
            catalog=subscription.catalog
        )
        detail.type = OrderDetailType.TRANSFER
        detail.subscription = subscription
        detail.amount = subscription.vendor_licenses
        detail.save()

    order_update(order)


def order_detail_policy_new(vendor_profile, detail):
    product = detail.product
    subscription = detail.subscription
    catalog = detail.catalog
    amount = detail.amount

    minimal_order = None
    expiry = None
    from_date = None
    to_date = None
    unit_price = None

    gsc_product_category = ProductCategory.objects.get(code='GSC')
    now = timezone.now()
    days_in_current_month = monthrange(now.year, now.month)[1]
    last_day_of_current_month = date(
        year=now.year,
        month=now.month,
        day=days_in_current_month
    )
    price = ProductCatalog.objects \
        .get(product=product, catalog=catalog).price

    if product is None:
        # We assume that we always have product or subscription for this
        # action type.
        product = subscription.product
    from_date = now
    if product.tier_number < 0 and product.category == gsc_product_category:
        minimal_order = 5
    else:
        minimal_order = 1
    if amount is None or amount < minimal_order:
        amount = max(vendor_profile.users, minimal_order)
    expiry = from_date + FrequencyEnum(product.plan.commitment).timedelta
    unit_price = price
    if product.plan.billing_frequency == product.plan.commitment:
        to_date = expiry
    else:
        if product.plan.billing_cycle == BillingCycleEnum.END_OF_MONTH:
            to_date = last_day_of_current_month
            days_left = _timedelta_to_days(
                last_day_of_current_month - from_date
            )
            unit_price = price * (days_left / days_in_current_month)
        elif product.plan.billing_cycle == BillingCycleEnum.DATE_TO_DATE:
            to_date = from_date + FrequencyEnum(product.plan.billing_frequency).timedelta
        else:
            raise ValueError(
                'Unhandled product plan\'s billing cycle "{}".'
                .format(product.plan.billing_cycle)
            )
    return {
        'minimal_order': minimal_order,
        'amount': amount,
        'expiry': expiry,
        'from_date': from_date,
        'to_date': to_date,
        'unit_price': unit_price,
        'extension': None,
        'refunded_amount': None
    }


def order_detail_policy_add(vendor_profile, detail):
    product = detail.product
    subscription = detail.subscription
    catalog = detail.catalog
    amount = detail.amount

    minimal_order = None
    expiry = None
    from_date = None
    to_date = None
    unit_price = None
    extension = None

    now = timezone.now()
    days_in_current_month = monthrange(now.year, now.month)[1]
    from_date = now

    product = subscription.product
    if not product.tier_number < 0:
        raise ValueError(
            'Only "per user"(product.tier_number < 0) product allowed.'
        )
    minimal_order = 1
    if amount is None or amount < minimal_order:
        if vendor_profile.users > subscription.vendor_licenses:
            amount = vendor_profile.users - subscription.vendor_licenses
        else:
            amount = minimal_order
    extension = timedelta(days=(
        (amount / (subscription.vendor_licenses + amount))
        * _timedelta_to_days(
            FrequencyEnum(product.plan.billing_frequency).timedelta
        )
    ))
    product_catalog = ProductCatalog.objects \
        .get(
            product=subscription.product,
            catalog=subscription.catalog,
        )
    if subscription.add_order == SubscriptionOrderAddStrategy.EXTEND:
        expiry = subscription.expiry_date + extension
        to_date = subscription.billing_cycle_end + extension
        unit_price = product_catalog.price
    elif subscription.add_order == SubscriptionOrderAddStrategy.PRORATE:
        expiry = subscription.expiry_date
        to_date = subscription.billing_cycle_end
        if product.plan.billing_frequency == FrequencyEnum.MONTH:
            unit_price = (
                float(product_catalog.price / days_in_current_month)
                * _timedelta_to_days(to_date - now) + 1
            )
        elif product.plan.billing_frequency == FrequencyEnum.YEAR:
            unit_price = (
                (product_catalog.price / 12)
                * (to_date.month - now.month + 1)
            )
        else:
            raise ValueError(
                'Unhandled product plan billing frequency "{}".'
                .format(product.plan.billing_frequency)
            )
    else:
        raise ValueError(
            'Unhandled subscription add strategy "{}".'
            .format(subscription.add_order)
        )
    return {
        'minimal_order': minimal_order,
        'amount': amount,
        'expiry': expiry,
        'from_date': from_date,
        'to_date': to_date,
        'unit_price': unit_price,
        'extension': _timedelta_to_days(extension),  # Result must be in days.
        'refunded_amount': None
    }


def order_detail_policy_upgrade(vendor_profile, detail):
    product = detail.product
    subscription = detail.subscription
    catalog = detail.catalog
    amount = detail.amount

    minimal_order = None
    expiry = None
    from_date = None
    to_date = None
    unit_price = None
    extension = None
    refunded_amount = None

    now = timezone.now()
    from_date = now
    days_in_current_month = monthrange(now.year, now.month)[1]
    last_day_of_current_month = date(
        year=now.year,
        month=now.month,
        day=days_in_current_month
    )

    subscription_product_price = subscription.product.productcatalog_set \
        .filter(catalog=subscription.catalog) \
        .first() \
        .price
    product_price = product.productcatalog_set \
        .filter(catalog=subscription.catalog) \
        .first() \
        .price
    if product.tier_number < 0:
        minimal_order = 1
        amount = 1
        extension = timedelta(days=(
            _timedelta_to_days(subscription.expiry_date - now)
            * float(subscription_product_price / product_price)
            * float(subscription.vendor_licenses / amount)
        ))
    else:
        minimal_order = min(subscription.vendor_licenses, vendor_profile.users)
        amount = max(
            subscription.vendor_licenses,
            vendor_profile.users
        ) if amount is None or amount < minimal_order else amount
        extension = timedelta(days=(
            _timedelta_to_days(subscription.expiry_date - now)
            * float(subscription_product_price / product_price)
        ))
    if subscription.upgrade_order == SubscriptionOrderUpgradeStrategy.REFUND:
        expiry = now + FrequencyEnum(product.plan.commitment).timedelta
    elif subscription.upgrade_order == SubscriptionOrderUpgradeStrategy.EXTEND:
        expiry = now + (FrequencyEnum(product.plan.commitment).timedelta + extension)
    else:
        raise ValueError(
                'Unhandled subscription upgrade strategy "{}".'
                .format(subscription.upgrade_order)
            )
    if product.plan.billing_frequency == product.plan.commitment:
        to_date = expiry
    else:
        if subscription.billing_cycle == BillingCycleEnum.END_OF_MONTH:
            to_date = last_day_of_current_month
        elif subscription.billing_cycle == BillingCycleEnum.DATE_TO_DATE:
            if subscription.upgrade_order == SubscriptionOrderUpgradeStrategy.EXTEND:
                to_date = from_date + (
                    FrequencyEnum(subscription.billing_frequency).timedelta
                    + extension
                )
            else:
                to_date = from_date + FrequencyEnum(
                    subscription.billing_frequency).timedelta
        else:
            raise ValueError(
                'Unhandled subscription billing cycle "{}".'
                .format(subscription.billing_cycle)
            )
    unit_price = product_price
    if subscription.plan.billing_frequency == FrequencyEnum.MONTH:
        refunded_amount = (
            (_timedelta_to_days(subscription.billing_cycle_end - now) - 1)
            / days_in_current_month
        ) * (subscription.vendor_licenses if product.tier_number < 0 else 1)
    elif subscription.plan.billing_frequency == FrequencyEnum.YEAR:
        refunded_amount = (
            (subscription.billing_cycle_end.month - now.month - 1)
            / 12
        ) * (subscription.vendor_licenses if product.tier_number < 0 else 1)
    else:
        raise ValueError(
                'Unhandled product plan billing frequency "{}".'
                .format(product.plan.billing_frequency)
            )
    return {
        'minimal_order': minimal_order,
        'amount': amount,
        'expiry': expiry,
        'from_date': from_date,
        'to_date': to_date,
        'unit_price': unit_price,
        'extension': _timedelta_to_days(extension),  # Result must be in days.
        'refunded_amount': refunded_amount
    }


def order_detail_policy_transfer(vendor_profile, detail):
    amount = detail.amount
    from_date = timezone.now()
    return {
        'minimal_order': None,
        'amount': amount,
        'expiry': None,
        'from_date': from_date,
        'to_date': None,
        'unit_price': None,
        'extension': None,
        'refunded_amount': None
    }


def order_detail_policy_renew(vendor_profile, detail):
    return {
        'minimal_order': None,
        'amount': None,
        'expiry': None,
        'from_date': None,
        'to_date': None,
        'unit_price': None,
        'extension': None,
        'refunded_amount': None
    }


ORDER_DETAIL_POLICIES_MAPPING = {
    OrderDetailType.NEW: order_detail_policy_new,
    OrderDetailType.ADD: order_detail_policy_add,
    OrderDetailType.UPGRADE: order_detail_policy_upgrade,
    OrderDetailType.TRANSFER: order_detail_policy_transfer,
    OrderDetailType.RENEW: order_detail_policy_renew
}


def create_order_instance(customer, name=None):
    if not name:
        name_pattern = 'Order of {customer_name} #{order_number}'
        last_order = Order.objects.filter(
            customer=customer,
            name__contains=name_pattern.format(
                customer_name=customer.name,
                order_number=''
            )
        ).order_by('-created_at').first()
        match_result = re.match(
            'Order of .+ #(?P<order_number>\d+)',
            last_order and last_order.name or ''
        )
        if match_result is not None:
            name = name_pattern.format(
                customer_name=customer.name,
                order_number=int(match_result.group('order_number')) + 1
            )
        else:
            name = name_pattern.format(
                customer_name=customer.name,
                order_number=customer.order_set.count() + 1
            )

    order = Order()
    order.customer = customer
    order.name = name
    order.currency = get_customer_currency(customer)
    order.status = OrderStatus.DRAFT

    return order


def order_update(order):
    order_detail_statuses = {detail.status for detail in order.details.all()}
    if not (order.status == OrderStatus.DRAFT
            and order_detail_statuses == {OrderStatus.DRAFT}):
        raise ValueError(
            'We can\'t edit order and order details which have status not "{}"'
            .format(OrderStatus.DRAFT)
        )
    for order_detail in order.details.all():
        order_detail_update(order_detail)
        order_detail.save()


def create_order_detail_instance(order, product, catalog):
    order_detail = OrderDetail()

    order_detail.order = order
    order_detail.product = product
    order_detail.catalog = catalog
    order_detail.status = OrderStatus.DRAFT

    return order_detail


def order_detail_update(order_detail):
    policy = ORDER_DETAIL_POLICIES_MAPPING.get(order_detail.type)
    if policy is None:
        raise ValueError(
            'Unhandled order detail type "{}".'.format(order_detail.type)
        )
    vendor_profile = VendorProfile.objects \
        .filter(customer=order_detail.order.customer) \
        .first()
    policy_data = policy(
        vendor_profile=vendor_profile,
        detail=order_detail
    )
    unit_price = policy_data['unit_price']
    if not unit_price:
        unit_price = ProductCatalog.objects.get(
            product=order_detail.product,
            catalog=order_detail.catalog
        ).price

    order_detail.amount = policy_data['amount']
    order_detail.sub_total = unit_price * policy_data['amount']
    order_detail.minimal_order = policy_data['minimal_order']
    order_detail.expiry = policy_data['expiry']
    order_detail.from_date = policy_data['from_date']
    order_detail.to_date = policy_data['to_date']
    order_detail.extension = policy_data['extension']
    order_detail.refunded_amount = policy_data['refunded_amount']
    order_detail.unit_price = unit_price
