import logging

from django.conf import settings
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)


def app_install(request):
    if settings.TEST_MODE is not True:
        return redirect("frontend:login")
    return render(request, template_name="sm/product/gsc/app-install.html", context=dict(
        admin_token=settings.SM_API_TOKEN
    ))
