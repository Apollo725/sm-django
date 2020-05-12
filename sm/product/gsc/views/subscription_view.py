# encoding: utf-8

from django.conf import settings
from django.core.mail import send_mail
from django.views import generic
from django.shortcuts import render
from django.utils.translation import ugettext as _

from sm.product.gsc import models
from sm.product.gsc import zoho
from sm.product.gsc.views.decorator_view import profile_required

import logging

from .helpers import extend_context, show_pricing_menu, get_reseller_link

logger = logging.getLogger(__name__)


class GenericView(generic.TemplateView):
    def get_context_data(self, **kwargs):
        kwargs = extend_context(kwargs)
        return super(GenericView, self).get_context_data(**kwargs)


class SubscriptionView(GenericView):
    template_name = "sm/frontend/subscriptions.html"

    class Context(object):
        def __init__(self, request):
            self.customer = request.user.sm.customer
            # fetches only GSC subscription
            self.subscription = models.SubscriptionManager(self.customer).ensure_exists()
            if self.subscription.product and self.subscription.product.tier_number > 1000:
                self.license_not_addable = True
            self.vendor_profile = models.get_vendor_profile(self.customer)
            self.product = self.subscription.product
            self.catalog = self.subscription.catalog
            self.product_catalog = models.ProductCatalog.objects.get(
                product=self.product,
                catalog=self.catalog)

            self.unit_price = "%.2f" % (
                self.product_catalog.price
            )

            self.unit_frequency = "/%s/%s" % (
                _('user') if self.product.tier_number < 0 else _('pack'),
                _('month') if self.product.plan == models.SubscriptionPlan.FLEX_PREPAID else _('year')
            )

            self.total_paid = models.calculate_total_paid(self.customer)

            if self.product.tier_number > 0:
                self.total_price = self.product_catalog.price
            else:
                self.total_price = self.subscription.vendor_licenses * self.product_catalog.price

            self.show_pricing_menu = show_pricing_menu(request)
            if self.customer.reseller:
                self.reseller_link = get_reseller_link(self.customer.reseller)

    def get(self, request, *args, **kwargs):
        context = self.Context(request)
        kwargs.update(context.__dict__)
        kwargs['GSC_PRODUCT_URL'] = settings.GSC_PRODUCT_URL
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.Context(request)
        subscription = context.subscription
        customer = context.customer
        if request.POST.get('update_renewal_option', None) == 'true':
            renewal_option = request.POST.get('renewal_option', None)
            if renewal_option == models.RenewalOption.CANCEL and subscription.renewal_option == models.RenewalOption.RENEW:
                subscription.renewal_option = renewal_option
                subscription.cancelled_by_user = True
                subscription.save(update_fields=['renewal_option', 'cancelled_by_user'])
                zoho.update_account(request.user.sm)
                logger.info("Renewal option is updated by %s to %s", customer, renewal_option)
                if models.PaypalTransaction.objects.filter(order=subscription.order).count() > 0:
                    # action takes when subscription are cancelled
                    self.on_paypal_subscriber_cancelled(subscription)

            elif renewal_option == models.RenewalOption.RENEW and subscription.paid:
                subscription.renewal_option = renewal_option
                subscription.cancelled_by_user = False
                subscription.save(update_fields=['renewal_option', 'cancelled_by_user'])
                zoho.update_account(request.user.sm)
                logger.info("Renewal option is updated by %s to %s", customer, renewal_option)

        kwargs.update(context.__dict__)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def on_paypal_subscriber_cancelled(self, subscription):
        paypal_tx = models.PaypalTransaction.objects.filter(order=subscription.order).first()
        subscription.vendor_status = models.VendorStatus.EVAL
        subscription.save(update_fields=['vendor_status'])
        send_mail(
            "[SM Alert] Paypal Subscription cancelled by %s" % subscription.customer,
            """Hi Danielle,

The customer {org_name} ({domain}) has cancelled his subscription to Shared Contacts for Gmail.

thanks to cancel his subscription from paypal@gmailsharedcontacts.com

His Subscription ID is : {subscr_id}

Link: https://www.paypal.com/webscr?cmd=_profile-recurring-payments&encrypted_profile_id={subscr_id}

Thank you !""".format(org_name=subscription.customer.verbose_name,
                      domain=subscription.customer.name,
                      subscr_id=paypal_tx.profile_id), None,
            settings.CANCEL_PAYPAL_SUBSCRIPTION_RECEIVER.split(","),
        )


@profile_required
def subscriptions(request):
    return SubscriptionView.as_view()(request)
