from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic import FormView

from sm.product.gsc import forms
from sm.product.gsc import models
from sm.product.gsc import zoho

from .decorator_view import profile_required

import logging

logger = logging.getLogger(__name__)


class RegistrationView(FormView):
    template_name = "sm/product/gsc/register.html"
    form_class = forms.RegistrationForm
    success_url = reverse_lazy("gsc:register-thanks")

    def __init__(self, **kwargs):
        super(RegistrationView, self).__init__(**kwargs)

    def get_success_url(self):
        return reverse("gsc:register-thanks")

    def get_user(self):
        """

        :rtype : sm.core.models.User
        """
        user = self.request.user.sm
        return user

    def get(self, request, *args, **kwargs):
        return super(RegistrationView, self).get(request, *args, **kwargs)

    def get_initial(self):
        user = self.get_user()
        return forms.RegistrationForm(user).get_initial()

    def form_valid(self, form):
        form.save()
        user = self.get_user()

        if not user.customer.org_name:
            profile = models.get_vendor_profile(user.customer)
            if profile.org_name:
                user.customer.org_name = profile.org_name
                user.customer.save()

        zoho.convert_lead(user)

        logger.info("Registration info is updated by %s", self.get_user().email)
        if 'referer_page' in self.request.session:
            referer_page = self.request.session['referer_page']
        else:
            referer_page = settings.GSC_PRODUCT_URL

        return render(self.request, template_name="sm/product/gsc/register-thanks.html", context=locals())

    def get_form_kwargs(self):
        kwargs = super(RegistrationView, self).get_form_kwargs()
        kwargs['user'] = self.get_user()
        return kwargs


@profile_required
def register(request):
    return RegistrationView.as_view()(request)
