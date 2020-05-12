from __future__ import absolute_import

import logging
from collections import OrderedDict

from django.http import response
from django.views.decorators.csrf import csrf_exempt

from sm.core.paypal.ipn import handle

logger = logging.getLogger(__name__)


@csrf_exempt
def webhook(request):
    logger.info("IPN message is received - %s", request.POST)
    handle(request.body, request.POST.copy())
    return response.HttpResponse()
