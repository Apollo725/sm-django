import os

os.environ.setdefault('PG_HOST', 'sm-services')
os.environ.setdefault('PG_DB_NAME', 'sm')
os.environ.setdefault('PG_USER', 'sm')
os.environ.setdefault('PG_PASSWORD', 'BPlyoGN3CFcsHzdc')
os.environ.setdefault('REDIS_HOST', 'sm-services')
os.environ.setdefault('GSC_PRODUCT_URL', 'https://app.gmailsharedcontacts.com')
os.environ.setdefault('GSC_API_TOKEN', '6hgsdrdovd58gj20unl7j3c1yhtywhp0')
os.environ.setdefault('SM_API_TOKEN', '0ssrbzlnpmoey7sy4azbqy47n3wvccqh')
os.environ.setdefault('SM_ROOT_NAME', 'root')
os.environ.setdefault('SM_ROOT_PASSWORD', 'ynvH4n8l5UHdc0g3')

# managed by stef@econsulting.fr
os.environ.setdefault('ZOHO_API_URL', 'https://crm.zoho.com')
os.environ.setdefault('ZOHO_API_TOKEN', 'cb4c619bb2f4b0d21147f474c8aafabb')

# paypal
os.environ.setdefault('PAYPAL_REST_API_MODE', 'live')
os.environ.setdefault('PAYPAL_REST_API_CLIENT_ID',
                      'AaEJpODCBdHjGoR4Z_ccp-YPCGq9mQ2y-_Yqn-M6PJBm08uUscMU4cvk6fvaFoQIJRMo8e-NXyybysRg')
os.environ.setdefault('PAYPAL_REST_API_SECRET',
                      'EAq-_Zh_ywowSt21lwnMC1xsvFrlxThVUI9IqaPvaZbuhjGWHMjqAaBqYL8Q72nJWSinm6ki7rCXULdm')

os.environ.setdefault('PAYPAL_IPN_SANDBOX', '')
os.environ.setdefault('PAYPAL_IPN_RECEIVER', 'paypal@gmailsharedcontacts.com')
os.environ.setdefault('DEBUG', 'False')

# braintree
os.environ.setdefault('BRAINTREE_MERCHANT_ID', '6hwtvjjwgc9574mq')
os.environ.setdefault('BRAINTREE_PUBLIC_KEY', 'dqbzvdvzfdvx58ps')
os.environ.setdefault('BRAINTREE_PRIVATE_KEY', '48c0165919a08a2560409a3e1c13f007')
os.environ.setdefault('BRAINTREE_SANDBOX', '')

os.environ.setdefault('LOGGING_FILE_NAME', 'production')

os.environ.setdefault('CANCEL_PAYPAL_PROFILE_RECEIVER',
                      'sm-alerts@gappsexperts.com,hoo@econsulting.fr')

os.environ.setdefault('RENEW_REPORT_RECEIVER',
                      'sm-alerts@gappsexperts.com,hoo@econsulting.fr')

os.environ.setdefault("SERVER_EMAIL", "noreply@gmailsharedcontacts.com")

os.environ.setdefault("CANCEL_PAYPAL_SUBSCRIPTION_RECEIVER", "sm-alerts@gappsexperts.com,hoo@econsulting.fr")

# noinspection PyUnresolvedReferences
from app.sharing_settings import *
