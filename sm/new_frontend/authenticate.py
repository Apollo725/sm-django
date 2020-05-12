from rest_framework.permissions import BasePermission

from sm.product.gsc import models


class HasProfile(BasePermission):
    """
    Allows access only to members who have profile.
    """

    def has_permission(self, request, view):
        user = request.user
        if getattr(user, 'sm', None):
            try:
                models.get_vendor_profile(user.sm.customer)
                return True
            except models.VendorProfileClazz.DoesNotExist:
                pass
        return False
