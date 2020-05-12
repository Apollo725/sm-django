from sm.product.gsc import models
from sm.frontend.decorators import *


def profile_required(function=None,
                     redirect_field_name=REDIRECT_FIELD_NAME,
                     login_url=None):
    def test_auth(user):
        if user.is_authenticated() and getattr(user, 'sm', None):
            try:
                models.get_vendor_profile(user.sm.customer)
                return True
            except models.VendorProfileClazz.DoesNotExist:
                pass
        return False

    return login_required(function, redirect_field_name, login_url, test_auth)