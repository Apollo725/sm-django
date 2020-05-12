from django.conf.urls import include, url

from sm.new_frontend.orders import views as orders_views
from sm.new_frontend.plans.views import ListPricingPlansView
from sm.new_frontend.profile.views.views import ProfileView
from sm.new_frontend.subscriptions import views as subscriptions_view

urlpatterns = [
    url(r'', include('sm.product.google.urls')),
    url('^subscriptions/?$', subscriptions_view.ListSubscriptionView.as_view(), name="list_subscription_view"),
    url('^display-plans/?$', ListPricingPlansView.as_view(), name="list_pricing_plans_view"),
    url('^vendor/detected-subscriptions/?$',
        subscriptions_view.UpsertDetectedSubscriptionView.as_view(),
        name="upsert_subscription_view"),
    url('^profile/?$', ProfileView.as_view(), name="profile_view"),
    url('^orders/$', orders_views.OrderListView.as_view(), name="order_list_view"),
    url('^order/<int:id>/$', orders_views.OrderRetrieveView.as_view(), name="order_retrieve_view"),
    url('^v2/order/(?P<id>\d+)/$', orders_views.OrderDetailView.as_view(), name="order_detail_view"),
    url('^v2/order/create/$', orders_views.OrderCreateView.as_view(), name="create_order_view"),
    url('^v2/order/update/$', orders_views.OrderUpdateView.as_view(), name="update_order_view"),
]
