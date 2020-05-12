from django.contrib import admin
from django.views.i18n import javascript_catalog
from django.contrib.admin import widgets
from django import forms
from django.views.generic import FormView
from django.contrib.admin.templatetags import admin_static
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.conf import settings
from mock_now import core


class MockNowForm(forms.Form):
    new_date = forms.SplitDateTimeField(
        widget=widgets.AdminSplitDateTime,
        label="Change current time")

    def save(self):
        core.set_mock_now(self.cleaned_data['new_date'])


class MockNowView(FormView):
    template_name = 'mock_now/index.html'
    form_class = MockNowForm

    def get_initial(self):
        return {
            'new_date': timezone.now(),
        }

    def form_valid(self, form):
        form.save()
        from django.contrib import messages
        messages.add_message(self.request,
                             messages.INFO,
                             "time is change successfully")
        return super(MockNowView, self).form_invalid(
            MockNowForm(initial=self.get_initial())
        )

    def get_context_data(self, **kwargs):
        data = super(MockNowView, self).get_context_data(**kwargs)
        data['title'] = "Mock now()"
        data['media'] = forms.Media(js=[admin_static.static('admin/js/' + js) for js in [
            'jquery.js',
            'jquery.init.js',
            'core.js',
            'actions.js'
        ]])
        data['current_time'] = timezone.now()
        data['site_title'] = "Test utilities"
        data['site_header'] = data['site_title']

        return data


class ResetDataForm(forms.Form):
    pass


class ResetDataView(MockNowView):
    form_class = ResetDataForm
    template_name = "mock_now/reset_data.html"

    def form_valid(self, form):
        from django.core.management import call_command
        call_command("flush", interactive=False)
        call_command("mocks")
        call_command("loaddata", "core/discount_codes")
        return super(ResetDataView, self).form_invalid(
            ResetDataForm()
        )

    def get_context_data(self, **kwargs):
        data = super(ResetDataView, self).get_context_data(**kwargs)
        data['title'] = 'Reset data'
        return data


def get_urls():
    urls = [
        url(r'^$', MockNowView.as_view(), name='mock_now'),
        url(r'^reset-data$', ResetDataView.as_view(), name="reset_data"),
        url(r'^jsi18n/$', javascript_catalog, {'packages': ('mock_now',)}, name='jsi18n')
    ]

    return (
        urls if settings.DEBUG else [],
        'mock_now',
        'mock_now'
    )
