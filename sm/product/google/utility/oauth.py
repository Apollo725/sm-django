import logging

import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession
from google.auth.exceptions import GoogleAuthError

from django.conf import settings

logger = logging.getLogger(__name__)


def get_authorized_session():
    """This function uses to google_auth library to authenticate with google.
    :return if no error is thrown, returns an authorized_session
        that can be used with the requests module.
        if an error is thrown the function returns None
    """
    try:
        credentials = google.oauth2.credentials.Credentials(
            settings.VENDOR_CONSOLES['mybonobo.info']['access_token'],
            **settings.VENDOR_CONSOLES['mybonobo.info']['credentials'])
    except GoogleAuthError as e:
        logger.exception("Google auth exception: {}".format(e.message))
        return None

    authorized_session = AuthorizedSession(credentials)
    logger.info(type(authorized_session))
    return authorized_session
