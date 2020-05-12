import decimal
import json

from braintree.exceptions.braintree_error import BraintreeError
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext as _

from sm.core import braintree_helper
from sm.core.paypal import billing_plan
from sm.core.paypal.billing_plan import dump_errors
from sm.product.gsc import charger
from sm.product.gsc import forms
from sm.product.gsc import mailer
from sm.product.gsc import models
from sm.product.gsc import subscription_manager
from sm.product.gsc import zoho
from sm.product.gsc import failed_transaction_manager
from sm.product.gsc.models import get_open_order_detail, OrderDetail
from .decorator_view import profile_required
from .helpers import extend_context

import logging

logger = logging.getLogger(__name__)


def get_checkout_type(subscription, order_detail):
    """
    :type order_detail: models.OrderDetail
    :type subscription: models.Subscription
    """
    if not subscription.paid:
        return "first"
    elif (order_detail.product.version != subscription.product.version or
          order_detail.product.plan != subscription.product.plan and
          order_detail.product.tier_number == -1):
        return "upgrade"
    elif order_detail.product.tier_number == -1:
        return "add"
    elif order_detail.product.tier_number > 0:
        return "upgradePack"
    else:
        raise Exception("can't determine checkout type")


def _is_tier_based(product):
    return True if product.tier_number > 0 else False


def get_checkout_type_verbose(checkout_type):
    return dict(
        upgrade="upgrade",
        add="add license",
        first="new subscription",
        upgradePack="upgrade package"
    ).get(checkout_type, "")


def get_discount_amount(request):
    from sm.core import promotion
    try:
        return promotion.validate_code(request.POST.get('promotion_code', '')).amount
    except promotion.Error:
        pass
    return 0


@profile_required
def checkout_thanks(request):
    return render(request, template_name="sm/product/gsc/checkout-thanks.html",
                  context=extend_context(locals()),
                  context_instance=RequestContext(request))


def post_checkout(request, customer, order_detail):
    """
    :type request: django.http.HttpRequest
    :type customer: models.Customer
    :type order_detail: models.OrderDetail
    """
    subscription = models.SubscriptionManager(customer).get_subscription()
    checkout_type = get_checkout_type(subscription, order_detail)
    contact_form = forms.ContactForm(request.user.sm, data=request.POST)
    catalog = subscription.catalog
    billing_form = forms.BillingDetailForm(
        instance=models.get_profile(customer) or models.Profile(customer=customer),
        data=request.POST
    )

    profile = None
    contact = None

    if contact_form.is_valid():
        contact = contact_form.save()
        customer.set_communication_user(request.user.sm, save=True)
    if billing_form.is_valid():
        profile = billing_form.save()

    if contact_form.is_valid() and billing_form.is_valid():
        zoho.update_contact(request.user.sm)
        zoho.update_account(request.user.sm)

        payment_method_nonce = request.POST.get('payment_method_nonce')
        payment_method_pk = request.POST.get('payment_method_token')
        if payment_method_pk:
            payment_method_instance = models.BraintreePaymentMethod.objects.filter(
                pk=payment_method_pk
            ).first()
            if payment_method_instance.customer != customer:
                logger.error("Customer %s is stealing payment method token from %s", customer,
                             payment_method_instance.customer)
                payment_method_instance = None
        else:
            payment_method_instance = None

        if payment_method_nonce or payment_method_instance:
            logger.info("Payment method received %s", request.user.sm.email)

            def get_amount():
                license_amount = request.POST.get('licenseAmount', None)
                if license_amount and license_amount.isdigit():
                    return int(license_amount)
                return None

            if not subscription.cancelled and subscription.order:
                last_payment_amount = subscription.order.sub_total
            else:
                last_payment_amount = 0

            customer_id = billing_plan.update_customer(request.user.sm)
            discount = decimal.Decimal(get_discount_amount(request))
            if customer_id:
                payment_total = 0
                extended_days = 0
                if checkout_type == 'first':
                    # get license amount
                    amount = get_amount()
                    if order_detail.product.version == models.ProductVersionEnum.BASIC:
                        payment_total = order_detail.total
                    else:
                        if _is_tier_based(order_detail.product):
                            if amount and amount >= 5 * order_detail.minimal_quantity:
                                tier = catalog.get_tier(amount,
                                                        version=order_detail.product.version,
                                                        plan=order_detail.product.plan)
                                order_detail.amount = amount
                                sub_total = tier.price
                                order_detail.sub_total = sub_total
                                order_detail.product = tier.product
                                order_detail.discount = sub_total * discount
                                payment_total = order_detail.sub_total
                                order_detail.save()
                            else:
                                logger.warn("invalid amount number: %s", amount)
                        else:
                            amount = get_amount()
                            if amount and amount >= 5 * order_detail.minimal_quantity:
                                order_detail.amount = amount
                                sub_total = amount * models.ProductCatalog.objects.get(
                                    product=order_detail.product,
                                    catalog=catalog
                                ).price
                                order_detail.sub_total = sub_total
                                order_detail.discount = sub_total * discount
                                payment_total = order_detail.total
                                order_detail.save()
                            else:
                                logger.warn("invalid amount number: %s", amount)

                elif checkout_type == 'upgrade':
                    amount = get_amount()
                    if amount and amount >= max(5 * order_detail.minimal_quantity,
                                                min(subscription.vendor_licenses, subscription.billable_licenses)):
                        remaining_days = models.get_remaining_days(subscription)
                        balance = last_payment_amount / remaining_days.total * remaining_days.remain
                        order_detail.amount = amount
                        sub_total = amount * models.ProductCatalog.objects.get(
                            product=order_detail.product,
                            catalog=catalog
                        ).price
                        order_detail.sub_total = sub_total
                        order_detail.discount = sub_total * discount
                        payment_total = order_detail.total
                        extended_days = int(balance / (payment_total / order_detail.product.get_commitment_days()))
                        order_detail.save()
                    else:
                        logger.warn("invalid amount number: %s", amount)
                elif checkout_type == 'add':
                    amount = get_amount()
                    if amount and amount > 0:
                        remaining_days = models.get_remaining_days(subscription)
                        balance = last_payment_amount / remaining_days.total * remaining_days.remain
                        order_detail.amount = amount
                        sub_total = amount * models.ProductCatalog.objects.get(
                            product=order_detail.product,
                            catalog=catalog
                        ).price
                        order_detail.sub_total = sub_total
                        payment_total = (
                                sub_total / remaining_days.total * remaining_days.remain - balance)
                        order_detail.discount = sub_total - payment_total
                        order_detail.save()
                    else:
                        logger.warn("invalid amount number: %s", amount)
                elif checkout_type == 'upgradePack':
                    amount = get_amount()
                    if amount and (amount > subscription.product.tier_number or (
                            amount >= subscription.product.tier_number and
                            order_detail.product.plan != subscription.product.plan)):
                        tier = catalog.get_tier(amount,
                                                version=order_detail.product.version,
                                                plan=order_detail.product.plan)
                        remaining_days = models.get_remaining_days(subscription)
                        balance = last_payment_amount / remaining_days.total * remaining_days.remain
                        order_detail.amount = amount
                        order_detail.sub_total = tier.price
                        order_detail.product = tier.product
                        payment_total = order_detail.sub_total
                        extended_days = int(balance / (payment_total / order_detail.product.get_commitment_days()))
                        order_detail.save()
                    else:
                        logger.warn("invalid amount number: %s", amount)

                if payment_total:
                    assert payment_total > 0, "invalid payment total: %s, order id: %s" % (
                        payment_total, order_detail.order.pk)
                    if checkout_type == 'add':
                        expiry_date = subscription.expiry_date
                    else:
                        expiry_date = (
                                models.calculate_expiration_date(monthly=order_detail.product.monthly) +
                                relativedelta(days=extended_days)
                        )

                    payment_total = float("%.2f" % payment_total)

                    payment_method = None

                    if payment_method_nonce:
                        payment_method = charger.create_payment_method(customer_id,
                                                                       profile,
                                                                       contact.name,
                                                                       payment_method_nonce,
                                                                       customer_name=customer.name)
                    elif payment_method_instance:
                        try:
                            payment_method = braintree_helper.get_payment_detail(payment_method_instance.token)
                        except BraintreeError as e:
                            error = dump_errors(e)
                            logger.error("Can't find braintree token %s, %s", payment_method_instance.token, error)

                            tx = failed_transaction_manager.create(
                                order_detail.order, "Can't find braintree token %s" % payment_method_instance.token)

                            zoho.update_failed_potential(
                                order_detail=order_detail,
                                failed_transaction=tx,
                                checkout_type=checkout_type
                            )

                            customer.set_last_payment_status(
                                outcome=error,
                                payment_id='braintree:None'
                            )

                    if payment_method:
                        result = charger.charge_order(payment_total, payment_method,
                                                      order_detail.order.id,
                                                      request.user.sm)
                        if result.is_success:
                            if (subscription.payment_gateway != "Braintree GAE" and
                                    models.PaypalTransaction.objects.filter(order__customer=customer).exists()):
                                mailer.cancel_paypal_profile(customer)

                            models.enable_payment_method(payment_method.token)

                            order_detail = subscription_manager.on_order_paid(
                                order_detail, expiry_date, checkout_type=checkout_type,
                                payment_id=result.transaction.id
                            )

                            if checkout_type == 'first':
                                order_detail.subscription.start_plan_date = timezone.now()
                                order_detail.subscription.save()
                            models.create_bt_transaction(order_detail.order, result.transaction.id)

                            request.session['checkout_success_type'] = checkout_type
                            return redirect(reverse("gsc:checkout-thanks"))
                        else:
                            error = billing_plan.dump_errors(result)

                            models.create_bt_transaction(
                                order_detail.order,
                                result.transaction.id if result.transaction else "",
                                error
                            )

                            models.disable_payment_method(payment_method.token)

                            tx = failed_transaction_manager.create(
                                order_detail.order,
                                error
                            )

                            zoho.update_failed_potential(
                                order_detail=order_detail,
                                failed_transaction=tx,
                                checkout_type=checkout_type
                            )

                            customer.set_last_payment_status(
                                outcome=error,
                                payment_id=("braintree:" + result.transaction.id) if result.transaction else "UNKNOWN"
                            )

                            customer.last_payment_type = checkout_type
                            customer.save()

            messages.error(request, _("We are sorry but your payment could not be processed. "
                           "Please try again or contact us on support@gmailsharedcontacts.com"))
            zoho.update_account(customer)


@profile_required
def checkout(request):
    requested_order_id = request.GET['order'] if 'order' in request.GET else None
    customer = request.user.sm.customer
    subscription = models.SubscriptionManager(customer).get_subscription()
    if requested_order_id:
        order_detail = OrderDetail.objects.filter(
            order__id=requested_order_id,
            order__customer=customer,
        ).first()
    else:
        order_detail = get_open_order_detail(customer)

    if subscription.paid and not order_detail:
        return redirect(reverse("gsc:subscriptions"))

    if not order_detail:
        return redirect("gsc:pricing")

    # this means "proceed to checkout" button was clicked
    if request.method == 'POST':
        response = post_checkout(request, customer, order_detail)
        if response:
            return response

    payment_method = models.find_payment_method(customer)
    if payment_method:
        if not payment_method.succeed:
            payment_method = None
    payment_method_type = payment_method.type if payment_method else ''

    contact_form = forms.ContactForm(request.user.sm)
    billing_form = forms.BillingDetailForm(
        instance=models.get_profile(customer) or models.Profile(customer=customer),
    )

    monthly = order_detail.product.plan == models.SubscriptionPlan.FLEX_PREPAID

    vendor_profile = models.get_vendor_profile(customer)
    product = order_detail.product
    tier = subscription.catalog.get_tier(product.tier_number, version=product.version, plan=product.plan)

    checkout_type = get_checkout_type(subscription, order_detail)
    # added as fix for SM-176
    is_tier_based = _is_tier_based(product)

    if checkout_type in ['add']:
        expiration_date = subscription.expiry_date
    else:
        expiration_date = models.calculate_expiration_date(monthly=product.monthly)

    available_tiers = []
    if is_tier_based:
        logger.info("product tier number %s", product.tier_number)
        if product.plan != subscription.product.plan:
            minimum_tier_number = product.tier_number - 1
        else:
            minimum_tier_number = product.tier_number

        available_tiers = subscription.catalog.get_available_tiers(
            version=product.version,
            plan=product.plan,
            minimum_tier_number=minimum_tier_number
        )
        available_tiers = [{'price': float(tier.price), 'number': tier.high, 'desc': tier.product.tier_name} for tier in
                           available_tiers]
        if requested_order_id:
            available_tiers = [available_tiers[0]]

    balance = 0
    last_payment_amount = subscription.get_last_payment_amount()
    remaining_days = models.get_remaining_days(subscription)
    logger.debug("Remaining days for %s %s", customer, remaining_days)
    if checkout_type in ['upgradePack', 'upgrade', 'add']:
        assert remaining_days is not None
        balance = last_payment_amount / remaining_days.total * remaining_days.remain

    if checkout_type == 'upgrade':
        minimum_licenses_to_upgrade = min(subscription.billable_licenses, subscription.vendor_licenses)
    else:
        if order_detail.minimal_quantity:
            minimum_licenses_to_upgrade = 5
        else:
            minimum_licenses_to_upgrade = 1

    order = order_detail.order

    order.name = "Gsc for %s (%s)" % (customer.name, get_checkout_type_verbose(checkout_type))
    order.save()

    return render(request, template_name="sm/product/gsc/checkout.html", context=extend_context({
        'monthly': monthly,
        'order_detail': order_detail,
        'subscription': subscription,
        'customer': customer,
        'vendor_profile': vendor_profile,
        'expiration_date': expiration_date,
        'commitment': _('1 year') if not monthly else _('1 month'),
        'tier': tier,
        'product': product,
        'balance': balance,
        'product_commitment_days': product.get_commitment_days(),
        'contact_form': contact_form,
        'billing_form': billing_form,
        'available_tiers': json.dumps(available_tiers),
        'remaining_days': 'null' if not remaining_days else json.dumps(remaining_days.to_json()),
        'checkout_type': checkout_type,
        'is_tier_based': is_tier_based,
        'minimum_licenses_to_upgrade': minimum_licenses_to_upgrade,
        'braintree_prefix': 'www' if not settings.BRAINTREE_SANDBOX else 'sandbox',
        'payment_method': payment_method,
        'payment_method_type': payment_method_type
    }))
