from __future__ import absolute_import
from django.conf import settings
import paypalrestsdk
from django.core.exceptions import ImproperlyConfigured

if not getattr(settings, 'PAYPAL_REST_API_MODE') or \
        not getattr(settings, 'PAYPAL_REST_API_CLIENT_ID') or \
        not getattr(settings, 'PAYPAL_REST_API_SECRET'):
    raise ImproperlyConfigured("PAYPAL API is not configured perperly")

api = paypalrestsdk.Api(
    dict(
        mode=settings.PAYPAL_REST_API_MODE,
        client_id=settings.PAYPAL_REST_API_CLIENT_ID,
        client_secret=settings.PAYPAL_REST_API_SECRET
    )
)

PAYPAL_API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

__all__ = ['api', 'PAYPAL_API_DATE_FORMAT']
