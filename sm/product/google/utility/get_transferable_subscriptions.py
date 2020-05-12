import logging

from requests.exceptions import RequestException

from .oauth import get_authorized_session
from sm.product.google.decorators import log_time


POLLING_URL = "https://www.googleapis.com/apps/reseller/v1/subscriptions"
logger = logging.getLogger(__name__)


@log_time
def get_transferable_subscriptions(customer_name, transfer_token):
    """This function send a request to the google API to retrieve user's subscriptions
    :param get_params:
    :return json dictionary containing status, error, error_message:
    """
    get_params = {
        'customerAuthToken': transfer_token,
        'customerId': customer_name,
        'maxResults': 100
    }

    error_dict = {
        'status': None,
        'error': True,
        'errorMessage': None
    }

    authorized_session = get_authorized_session()
    if not authorized_session:
        error_dict['status'] = 500
        error_dict['errorMessage'] = 'Google authentication error.'
        logger.error('Google authentication error for customer {}'.format(get_params['customerId']))
        return error_dict

    try:
        response = authorized_session.get(POLLING_URL, params=get_params)
        complete_json = returned_json = response.json()
        while 'nextPageToken' in returned_json:
            get_params['nextPageToken'] = returned_json['nextPageToken']
            returned_json = authorized_session.get(POLLING_URL, params=get_params).json()
            for sub in returned_json['subscriptions']:
                complete_json['subscriptions'].append(sub)
    except RequestException:
        error_dict['status'] = 500
        error_dict['errorMessage'] = 'Request error.'
        logger.exception('Request error for customer {}'.format(get_params['customerId']))
        return error_dict

    if response.status_code == 403:
        error_dict['status'] = 403
        error_dict['errorMessage'] = 'Transfer token in not valid.'
        logger.info('Transfer token in not valid for customer {}'.format(get_params['customerId']))
        return error_dict
    elif response.status_code != 200:
        error_dict['status'] = response.status_code
        error_dict['errorMessage'] = 'An Error has occurred'
        logger.info('An error has occurred for customer {}'.format(get_params['customerId']))
        return error_dict

    #TODO do we need this?
    complete_json['error'] = False
    complete_json['error_message'] = None

    return complete_json
