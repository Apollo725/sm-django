from django.contrib import messages
from django.shortcuts import render

from sm.product.gsc import models
from sm.product.gsc import forms
from sm.product.gsc import zoho
from .decorator_view import profile_required
from .helpers import extend_context, show_pricing_menu


@profile_required
def profile_view(request):
    is_post = request.method == 'POST'
    customer = request.user.sm.customer
    subscription = models.SubscriptionManager(customer).get_subscription()
    contact_form = forms.ContactForm(
        request.user.sm,
        data=request.POST if is_post else None
    )
    billing_form = forms.BillingDetailForm(
        instance=models.get_profile(customer) or models.Profile(customer=customer),
        data=request.POST if is_post else None
    )

    if is_post:
        if contact_form.is_valid():
            contact_form.save()
            customer.set_communication_user(
                request.user.sm, save=True
            )
        if billing_form.is_valid():
            billing_form.save()
        updated = contact_form.is_valid() and billing_form.is_valid()
        if updated:
            messages.add_message(request, messages.INFO, "Saved successfully")
            zoho.update_account(request.user.sm)
            zoho.update_contact(request.user.sm)

    return render(request, template_name="sm/frontend/profile.html", context=extend_context({
        'subscription': subscription,
        'customer': customer,
        'contact_form': contact_form,
        'billing_form': billing_form,
        'show_pricing_menu': show_pricing_menu(request)
    }))
