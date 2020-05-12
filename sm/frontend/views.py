import re

from django.core.urlresolvers import reverse, RegexURLPattern
from django.shortcuts import render, redirect
# Create your views here.
from .decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout as dj_logout, login as dj_login, REDIRECT_FIELD_NAME
from sm.core.auth import AUTH_TOKEN_KEY
from django.conf import settings
from django.core.management import call_command
from sm.core.models import User
from sm.product.gsc.views.decorator_view import profile_required
import logging

logger = logging.getLogger(__name__)

__all__ = ['index', 'login', 'logout', 'pages', 'react_base_view']


@login_required
def index(request):
    from sm.product.gsc.urls import urlpatterns as gsc
    from sm.frontend.urls import urlpatterns as frontend

    urls = {
        'gsc': [url for url in gsc if isinstance(url, RegexURLPattern) and
                url.name in ['pricing', 'checkout', 'subscriptions']],

        'frontend': [url for url in frontend if isinstance(url, RegexURLPattern) and
                     url.name in ['index', 'pages', 'logout', 'login']]
    }
    # return render(request, template_name="sm/frontend/index.html", context={'urls': urls})
    return redirect("gsc:subscriptions")


def sm_authenticate(user_token):
    from sm.core.user_token import user_token_factory
    token = user_token_factory.get(user_token)
    user_token_factory.remove(user_token)
    if token:
        user = User.objects.filter(email=token.email, customer__name=token.customer).first()
        if user:
            return user.auth_user


def pages(request, page=None):
    if not page:
        return redirect(reverse("frontend:pages", kwargs={'page': 'sample'}))
    return render(request, template_name="sm/frontend/pages/%s.html" % page)


# TODO: Fix login with get.
def login(request):
    dj_logout(request)
    try:
        token = request.GET[AUTH_TOKEN_KEY]
        user = sm_authenticate(user_token=token)

        if user:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            dj_login(request, user)
            if 'referer' in request.GET:
                request.session['referer_page'] = request.GET['referer']

            return redirect(request.GET.get(
                REDIRECT_FIELD_NAME, reverse("frontend:index")))
    except KeyError:
        pass

    if settings.DEBUG:
        mock_users = User.objects.filter(mock=True).order_by('created_at')

    gsc_url = request.GET.get('gsc_url', settings.GSC_PRODUCT_URL)
    if settings.TEST_MODE:
        abs_path = request.build_absolute_uri("/")
        admin_token = settings.SM_API_TOKEN
    else:
        abs_path = re.sub('^http', 'sm', request.build_absolute_uri("/"))
    test_mode = settings.TEST_MODE
    install_path = reverse("gsc:app_install")
    page_class = "login-page"
    return render(request, template_name="sm/frontend/login.html", context=locals())


def logout(request):
    dj_logout(request)
    return redirect(reverse('frontend:login'))


@user_passes_test(lambda u: u.is_superuser)
def crons(request):
    if 'cron' in request.GET:
        cron = request.GET['cron']
        if 'Create SalesOrders' in cron:
            call_command('runcrons', 'sm.core.cron_jobs.CreateSalesOrdersCronJob', force=True)
        if 'Renew Customers' in cron:
            call_command('runcrons', 'sm.product.gsc.cron.RenewCustomers', force=True)

    cron_list = ('Create SalesOrders', 'Renew Customers',)
    return render(request, template_name="sm/frontend/crons.html", context=dict(
        crons = cron_list
    ))


def reseller(request, reseller_name=None):
    return render(request, template_name="sm/frontend/reseller.html", context=dict(
        reseller_name=reseller_name
    ))


@profile_required
def react_base_view(request):
    return render(request, 'sm/frontend/react_base.html')
