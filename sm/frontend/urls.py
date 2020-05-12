from django.conf.urls import url, include

from sm.frontend import views
from sm.frontend.webhooks import urls as webhooks
from sm.frontend.webhooks.views import paypal
from sm.frontend.views import react_base_view


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/login/?$', views.login, name='login'),
    url(r'^accounts/logout/?$', views.logout, name='logout'),
    url(r'^pages/(?P<page>[a-z0-9A-Z_\-]+)?$', views.pages, name='pages'),
    url(r'^webhooks/', include(webhooks, namespace='webhooks')),
    url(r'^ipn_process/?', paypal, name='ipn_process'),
    url(r'^reseller/(?P<reseller_name>[^/]+)', views.reseller, name='reseller-page'),
    url(r'^crons/?$', views.crons, name='crons'),
    url('^react51/', react_base_view, name='react_base'),
]
