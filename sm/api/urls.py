from __future__ import absolute_import

from django.conf.urls import url, include

from . import views

urlpatterns = [
    # token api
    url('^userTokens/(?P<customer>[^/]+)/(?P<email>[^/]+)/?$',
        views.TokenView.as_view({'get': 'retrieve'}), name='user-token-detail'),
    url('^userTokens/(?P<email>[^/]+)/?$', views.TokenView.as_view({'get': 'retrieve'})),
    url('^btToken/?$', views.BraintreeTokenView.as_view({'post': 'create'}), name='bt-token'),
    url('^promotion/?$', views.PromotionCodeView.as_view({'get': 'retrieve'}), name='promotion-code'),
    url('^customers/resellers/?$', views.ResellerView.as_view({'get': 'list'}), name='reseller'),
    url('^reseller/register/?$', views.ResellerRegisterView.as_view({'post': 'create'})),
    url('^reseller/approve/?$', views.ResellerApproveView.as_view()),
    url('^products/gsc/', include('sm.product.gsc.api.urls', namespace="gsc")),
]
