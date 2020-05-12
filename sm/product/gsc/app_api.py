from __future__ import absolute_import

import logging

import requests
from django.conf import settings
from requests import RequestException
from sm.product.gsc.models import put_mock_gsc_license

logger = logging.getLogger(__name__)


def update_license(subscription):
    json = dict(
        domain=subscription.domain,
        plan=subscription.product.version,
        status=subscription.vendor_status,
        licenseNumber=subscription.vendor_licenses
    )

    try:

        if settings.TEST_MODE:
            result = put_mock_gsc_license(subscription)
            if result.pk is not None:
                logger.info("Push subscription %s to gsc successfully", json)
            else:
                logger.error(
                    "Failed to push subscription to gsc %s",
                    json
                )
            return

        response = requests.post(
            settings.GSC_PRODUCT_URL + "/admin/api/license",
            json=json,
            headers=dict(
                authorization='GSC-TOKEN ' + settings.GSC_API_TOKEN
            )
        )

        if response.status_code == 200:
            logger.info("Push subscription %s to gsc successfully", json)
        else:
            logger.error(
                "Failed to push subscription to gsc %s: %s\n %s",
                json, response.status_code, response.content.decode('utf-8')
            )
    except RequestException as e:
        logger.exception("Failed to push subscription to gsc %s: %s", json, e.message)
