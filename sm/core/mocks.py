from __future__ import absolute_import
# create mock data

# create super user
from django.contrib.auth.models import User as AuthUser
from rest_framework.authtoken import models


def mock():
    from django.conf import settings
    if not AuthUser.objects.filter(username=settings.SM_ROOT_NAME).exists():
        AuthUser.objects.create_superuser(
            email=None,
            username=settings.SM_ROOT_NAME,
            password=settings.SM_ROOT_PASSWORD
        )

    models.Token.objects.filter(
        user__username=settings.SM_ROOT_NAME
    ).update(key=settings.SM_API_TOKEN)
