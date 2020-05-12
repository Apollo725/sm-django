from .profile_view import profile_view
from .payment_method_view import payment_information
from .license_view import license_add
from .register_view import register
from .checkout_view import checkout, checkout_thanks
from .uninstall_view import uninstalled
from .subscription_view import subscriptions
from .pricing_view import pricing
from .app_install_view import app_install


__all__ = [
    'profile_view',
    'payment_information',
    'license_add',
    'register',
    'checkout',
    'checkout_thanks',
    'uninstalled',
    'subscriptions',
    'pricing',
    'app_install',
]
