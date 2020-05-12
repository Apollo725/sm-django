from django.conf.urls import url

from sm.product.gsc import views
from sm.product.gsc.views.invoices_view import InvoiceListView, InvoiceRetrieveView


urlpatterns = [
    url('^register/?$', views.register, name='register'),
    url('^pricing/?$', views.pricing, name='pricing'),
    url('^invoices/?$', view=InvoiceListView.as_view()),
    url('^invoices/(?P<invoice_id>\d+)$', view=InvoiceRetrieveView.as_view(), name='invoices'),
    url('^license-add/?$', views.license_add, name='license-add'),
    url('^checkout/?$', views.checkout, name='checkout'),
    url('^checkout-thanks/?$', views.checkout_thanks, name='checkout-thanks'),
    url('^subscriptions/?$', views.subscriptions, name='subscriptions'),
    url('^uninstalled/?$', views.uninstalled, name='uninstalled'),
    url('^payment-information/?$', views.payment_information, name='payment-information'),
    url('^profile/?$', views.profile_view, name='profile'),
    url('^accounts/appInstall/?$', views.app_install, name='app_install')
]
