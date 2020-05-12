from django.conf.urls import url

from sm.product.gsc.api import views, apiview

urlpatterns = [
    url(r'^subscriptions/(?P<customer>[^/]+)$',
        views.SubscriptionDetailView.as_view({'get': 'retrieve', 'put': 'update'}), name='subscription-detail'),

    # GSC Account API
    # GET,PUT /api/product/gsc/[domain_name]/[email]
    url(r'^users/(?P<customer>[^/]+)/(?P<email>[^/]+)$',
        views.AccountUpdateView.as_view({'put': 'update', 'get': 'retrieve'}), name="user-detail"),

    url(r'^users/sign_in$', apiview.UserView.as_view({'post': 'create'}), name="user-sign-in"),

    url(r'^users/(?P<id>\d+)?$', apiview.UserView.as_view({'put': 'update'}), name="user-update"),

    url(r'^profiles/(?P<customer>[^/]+)$',
        views.ProfileUpdateView.as_view({'put': 'update', 'get': 'retrieve'}), name="profile-detail"),

    url(r'^vendorProfiles/(?P<customer>[^/]+)$',
        views.VendorProfileUpdateView.as_view({'put': 'update', 'get': 'retrieve'}), name="vendor-profile-detail"),

    url(r'^firstShare/?$', views.FirstShareView.as_view({'post': 'update'}), name="first-share"),
    # Used only in test mode
    url(r'^installState/?$', apiview.UserView.as_view({'get': 'install_state'}), name="install-state")
]
