from django.conf.urls import url

from sm.frontend.webhooks import views

urlpatterns = [
    url('^paypal/?$', views.paypal, name='paypal')
]
