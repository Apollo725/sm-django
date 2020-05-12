from __future__ import absolute_import

from django.conf.urls import url

from sm.product.google.views.vendor_token_check_view import VendorTokenCheckView

urlpatterns = [
    url("^check-vendor-token/?$", view=VendorTokenCheckView.as_view(), name="check_vendor_token"),
]
