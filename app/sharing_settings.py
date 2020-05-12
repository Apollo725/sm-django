import os
import sys

from django.utils.translation import ugettext_lazy as _


def __(key, default):
    return os.environ[key] if key in os.environ else default


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TESTING = 'test' in sys.argv
# GSC
GSC_PRODUCT_URL = __('GSC_PRODUCT_URL', 'http://staging-app.gmailsharedcontacts.com')
GSC_API_TOKEN = __('GSC_API_TOKEN', '2AV1u38gaQBwW54Xf3ficI6bbJPZJCOf')
SM_API_TOKEN = __('SM_API_TOKEN', '52e24734b66e66ea1ad596f084e87f379a3927b3')
SM_ROOT_NAME = __('SM_ROOT_NAME', 'root')
SM_ROOT_PASSWORD = __('SM_ROOT_PASSWORD', 'notasecret')
LOGGING_FILE_NAME = __('LOGGING_FILE_NAME', 'development')

# ZOHO
ZOHO_API_URL = __('ZOHO_API_URL', 'https://crm.zoho.com')
ZOHO_API_TOKEN = __('ZOHO_API_TOKEN', 'cb4c619bb2f4b0d21147f474c8aafabb')  # use production setting instead
# ZOHO_API_TOKEN = __('ZOHO_API_TOKEN', '3f3e994d7da6093400499160589c8c4b') # standar version of zoho crm can't add customize fields

# managed by paypal@gmailsharedcontacts.com
# https://developer.paypal.com/developer/applications/edit/QWFFSnBPRENCZEhqR29SNFpfY2NwLVlQQ0dxOW1RMnktX1lxbi1NNlBKQm0wOHVVc2NNVTRjdms2ZnZhRm9RSUpSTW84ZS1OWHl5YnlzUmc=
PAYPAL_REST_API_MODE = __('PAYPAL_REST_API_MODE', 'sandbox')
PAYPAL_REST_API_CLIENT_ID = __('PAYPAL_REST_API_CLIENT_ID',
                               'Aa7sKCns8hJ0N9IoL3Dh2aGBH-2OkkN2aZ-YMnAXQ72_Pt25MaxFLaA-a6YYlh-ms1E1lt7Rj1JogH9z')
PAYPAL_REST_API_SECRET = __('PAYPAL_REST_API_SECRET',
                            'EEtGrPe71euOYTW0alzEl6XM2W9X0e0b8P0-WjXfljOs3nKWP8aBT4RqFN4gwRIrN531Q2QdqY0ie4Qd')

PAYPAL_IPN_SANDBOX = __('PAYPAL_IPN_SANDBOX', True)
PAYPAL_IPN_RECEIVER = __('PAYPAL_IPN_RECEIVER', 'marketing@econsulting.fr')

# managed by hoozecn.bt.2015:hoozecn.bt.2015
# https://sandbox.braintreegateway.com/merchants/gf856z86skfbjqsv/home
BRAINTREE_MERCHANT_ID = __('BRAINTREE_MERCHANT_ID', 'gf856z86skfbjqsv')
BRAINTREE_PUBLIC_KEY = __('BRAINTREE_PUBLIC_KEY', '86bh5nst63bnqnkm')
BRAINTREE_PRIVATE_KEY = __('BRAINTREE_PRIVATE_KEY', '73d164bfe50a03cefee132f0448ccd42')
BRAINTREE_SANDBOX = __('BRAINTREE_SANDBOX', True)

PG_DB_NAME = __('PG_DB_NAME', 'sm')
PG_USER = __('PG_USER', 'postgres')
PG_HOST = __('PG_HOST', 'sm-services')
PG_PORT = str(int(__('PG_PORT', '5432')))
PG_PASSWORD = __('PG_PASSWORD', '')

REDIS_HOST = __('REDIS_HOST', 'sm-services')
REDIS_PORT = str(int(__('REDIS_PORT', '6379')))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (__('DEBUG', 'True')).lower() != 'false'

ALLOWED_HOSTS = ['billing.gappsexperts.com']

GRAPPELLI_ADMIN_HEADLINE = "Subscription Manager"
GRAPPELLI_ADMIN_TITLE = "SM Console"

# Application definition

INSTALLED_APPS = (
    'django_cron',
    'dal',
    'dal_select2',
    'corsheaders',
    'mock_now',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sm.core',
    'sm.api',
    'sm.frontend',
    'sm.new_frontend',
    'sm.product.gsc',
    'sm.test',
    'sm.product.google',
    'django_extensions',
    'rest_framework',
    'django_filters',
    'mathfilters',
    'rest_framework.authtoken',
    'django_mocks',
    'compressor',
    'zoho_api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    # 'threadlocals.middleware.ThreadLocalMiddleware'  # not used
)

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
                'django_request2context.request2context',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': PG_DB_NAME,
        'USER': PG_USER,
        'PASSWORD': PG_PASSWORD,
        'HOST': PG_HOST,
        'PORT': PG_PORT
    }
}

REDIS_LOCATION = ":".join([REDIS_HOST, REDIS_PORT])

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.ShardedRedisCache',
        'LOCATION': REDIS_LOCATION,
        'OPTIONS': {
            'DB': '0',
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
    ('de', _('German')),
    ('es', _('Spanish')),
    ('he', _('Hebrew')),
    ('it', _('Italian')),
    ('ru', _('Russian')),
    ('pt', _('Portuguese')),
    ('ko', _('Korean')),
    ('ja', _('Japanese')),
)

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'conf', 'locale')
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',  # Any other renders
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),

    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',  # Any other parsers
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

# session
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_URL = 'redis://' + REDIS_LOCATION
SESSION_REDIS_PREFIX = 'sm:session'
SESSION_COOKIE_HTTPONLY = False

# celery
CELERY_RESULT_BACKEND = 'redis://' + REDIS_LOCATION
BROKER_URL = 'redis://' + REDIS_LOCATION
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

LOGGING_CONFIG = None

# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
TEST_RUNNER = 'sm.product.google.existing_db_testrunner.ExistingDBTestRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
NOSE_ARGS = [
    # '--with-coverage',
    '--cover-package=sm',
]

SECRET_KEY = '6(=7jpo3&9l6b(b$*c8@sdkmyc0!a+gi=)n+qwh!uq19@d47%@'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

RUN_SALES_ORDERS_CRON_JOB_AT_TIME = '15:00'
SALES_ORDERS_CRON_JOB_TIME_RANGE_HOURS = 24
SALES_ORDERS_RUN_EVERY_MIN = 10
CRON_CLASSES = ['sm.product.gsc.cron.RenewCustomers', 'sm.core.cron_jobs.CreateSalesOrdersCronJob']
DJANGO_CRON_LOCK_TIME = 9000

INVOICE_PER_PAGE = 10

import logging.config

logging.config.fileConfig(
    os.path.join(BASE_DIR, 'app', 'logging', LOGGING_FILE_NAME + '.ini'),
    disable_existing_loggers=False
)

if 'pydev_host' in os.environ:
    sys.path.append(os.path.join(BASE_DIR, 'pycharm-debug.egg'))
    import pydevd

    hosts = os.environ['pydev_host'].split(':')
    host = hosts[0]
    port = int(hosts[1]) if len(hosts) > 1 else 7777

    sys.stdout.write("Connecting to debug server: %s:%s\n" % (host, port))

    pydevd.settrace(host,
                    port=port,
                    stdoutToServer=True,
                    stderrToServer=True,
                    suspend=False)
    sys.stdout.write("Connect to debug server: OK\n")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Host for sending e-mail.
EMAIL_USE_TLS = __('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST = __('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = __('EMAIL_HOST_USER', 'noreply@gmailsharedcontacts.com')
EMAIL_HOST_PASSWORD = __('EMAIL_HOST_USER', '@2mopCR!')
EMAIL_PORT = int(__('EMAIL_PORT', '587'))

if 'USE_DOCKER' in os.environ:
    EMAIL_HOST = 'mail'
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False

DEFAULT_PRODUCT_CODE_TRIAL_SUBSCRIPTION = 'gsc_enterprise_annual_yearly'

DEFAULT_FROM_EMAIL = __("DEFAULT_FROM_EMAIL", "noreply@gmailsharedcontacts.com")
RENEW_REPORT_RECEIVER = __('RENEW_REPORT_RECEIVER', "hoo@econsulting.fr")
CANCEL_PAYPAL_PROFILE_RECEIVER = __('CANCEL_PAYPAL_PROFILE_RECEIVER', "hoo@econsulting.fr")
ERROR_RECEIVER = __('ERROR_RECEIVER', "hoo@econsulting.fr")
SERVER_EMAIL = __("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
ADMINS = [(admin.split(",")[0], admin.split(",")[-1]) for admin in __("ADMINS", "SM Errors,sm-errors@gappsexperts.com").split(";")]
CANCEL_PAYPAL_SUBSCRIPTION_RECEIVER = __('CANCEL_PAYPAL_SUBSCRIPTION_RECEIVER', "hoo@econsulting.fr")

# CORS_ORIGIN_REGEX_WHITELIST https://github.com/ottoyiu/django-cors-headers/

CORS_ORIGIN_REGEX_WHITELIST = (r'.*', )

TEST_MODE = False
# if 'test' in sys.argv:
import environ

env = environ.Env()
env.read_env('.env')
if env('TEST_MODE') != 'off':
    TEST_MODE = True

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
# Django debug toolbar
# To find the correct docker inspect <sm_runtime> | grep -e '"Gateway"'
# Where <sm_runtime> is the Docker container that is running Django.
INTERNAL_IPS = ['172.19.0.1', '172.18.0.1']

VENDOR_CONSOLES = {
    'mybonobo.info': {
        # MB prefix is for mybonobo.info
        'access_token': __('MB_ACCESS_TOKEN',
                           'ya29.GltZBWqDmYTwReKJlQgrVz79TlnJTi0OSlDYJouo2jRA9HTg2f4ImQ2G3lkfDJPOvxPlTBI-WRDOTdWbZdWte1Xb5qr7JaxDNaKnVsRoDePqXFuIDU4saW3wKFbh'),
        'credentials': {
            'refresh_token': __('MB_REFRESH_TOKEN',
                                '1/PVbYa0mEdrnhn_DR3Im4nBXFCAG8JQ3FAOVIg3DRGmZYEj3HaMQYpo7stuRYOUDR'),
            'token_uri': __('TOKEN_URI', 'https://accounts.google.com/o/oauth2/token'),
            'client_id': __('MB_CLIENT_ID', '643378504561-914auf1hs0v6vcp1tfa2hbdd2o1pdeiu.apps.googleusercontent.com'),
            'client_secret': __('MB_CLIENT_SECRET', '4qWoD7DAOJcVyvCsunLEa5pS')
        }
    },
    'econsulting.fr': {
        # EC prefix is for econsulting.fr
        'access_token': __('EC_ACCESS_TOKEN', ''),
        'credentials': {
            'refresh_token': __('EC_REFRESH_TOKEN', ''),
            'token_uri': __('TOKEN_URI', ''),
            'client_id': __('EC_CLIENT_ID', ''),
            'client_secret': __('EC_CLIENT_SECRET', '')
        }
    },
    'canada.gappsexperts.com': {
        # CA prefix is for canada.gappsexperts.com
        'access_token': __('CA_ACCESS_TOKEN', ''),
        'credentials': {
            'refresh_token': __('CA_REFRESH_TOKEN', ''),
            'token_uri': __('TOKEN_URI', ''),
            'client_id': __('CA_CLIENT_ID', ''),
            'client_secret': __('CA_CLIENT_SECRET', '')

        }
    }
}

