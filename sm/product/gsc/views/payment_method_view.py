from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

from sm.core.paypal import billing_plan
from sm.product.gsc import charger
from sm.product.gsc import models

from .decorator_view import profile_required
from .helpers import extend_context, show_pricing_menu


@profile_required
def payment_information(request):
    customer = request.user.sm.customer

    if request.method == 'POST':
        payment_method_nonce = request.POST.get('payment_method_nonce')
        if payment_method_nonce:
            profile = models.get_profile(customer)
            contact = request.user.sm
            customer_id = billing_plan.update_customer(request.user.sm)
            payment_method = charger.create_payment_method(customer_id,
                                                           profile,
                                                           contact.name,
                                                           payment_method_nonce,
                                                           customer_name=customer.name)
            if payment_method:
                models.enable_payment_method(payment_method.token)
                subscription = models.SubscriptionManager(customer).get_subscription()
                subscription.payment_gateway = 'Braintree GAE'
                subscription.save()
            else:
                messages.warning(request, "Can't validate your payment method, please try with another one")
        return redirect(reverse('gsc:payment-information'))

    payment_method = models.find_payment_method(customer)
    validate_card_types = ['credit_card', 'paypal']

    return render(request,
                  template_name="sm/frontend/payment-information.html",
                  context=extend_context({
                      'show_pricing_menu': show_pricing_menu(request),
                      'payment_method': payment_method,
                      'validate_card_types': validate_card_types
                  }))
