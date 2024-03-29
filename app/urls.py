"""sm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

import mock_now.admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^test/mock_now/', include(mock_now.admin.get_urls())),
    url(r'^api/', include('sm.api.urls', namespace="api")),
    url(r'', include('django.conf.urls.i18n')),
    url(r'', include('sm.frontend.urls', namespace="frontend")),
    url(r'^api/', include('sm.new_frontend.urls', namespace="new_frontend")),
    url(r'', include('sm.product.urls')),
]

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         url(r'^__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
