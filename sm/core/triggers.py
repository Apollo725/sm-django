from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import *
from django.contrib.auth.models import User as auth_user_model
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def update_name(instance=None, **kwargs):
    if kwargs.get('raw'):
        return

    assert isinstance(instance, User)
    if not instance.name:
        instance.name = instance.email


@receiver(post_save, sender=User)
def create_auth_user(instance=None, created=False, **kwargs):
    if kwargs.get('raw'):
        return

    assert isinstance(instance, User)

    def get_user_name(user):
        assert isinstance(user, User)
        import re
        prefix = (user.email or "").split("@")[0][:12].lower()
        prefix = re.sub('[^a-z0-9_\-]', '_', prefix)

        def gen_user_name():
            from uuid import uuid4
            return (prefix + "_" + uuid4().hex)[:20]

        while True:
            username = gen_user_name()
            if auth_user_model.objects.filter(username=username).exists():
                continue
            return username

    if created:
        names = instance.name.split(" ")
        auth_user = auth_user_model.objects.create_user(
            username=get_user_name(instance), email=instance.email.lower(),
            first_name=names[0].strip(),
            last_name=names[-1].strip()
        )
        instance.auth_user = auth_user
        instance.save(update_fields=['auth_user'])
        logger.debug("%s is created", instance)


@receiver(post_save, sender=auth_user_model)
def create_token_for_staff(instance, created=False, **kwargs):
    if kwargs.get('raw'):
        return

    if created and instance.is_superuser:
        import rest_framework.authtoken.models
        token = rest_framework.authtoken.models.Token.objects.create(
            user=instance
        )

        import sys
        from django.conf import settings
        if (len(sys.argv) > 1 and sys.argv[1] == 'test') or settings.DEBUG:
            logger.info("Auth token for %s is created: %s", instance, token.key)


@receiver(post_save)
def update_crm(sender, instance=None, created=False, **kwargs):
    if kwargs.get('raw'):
        return

    models = [Profile, VendorProfile]
    if sender in models:
        logger.info("%s is updated", getattr(instance, 'customer', None))
