from __future__ import absolute_import

import logging

import requests
from django.conf import settings
from django.core import exceptions
from django.http import Http404
from django.utils.timezone import now
from rest_framework import generics, mixins
from rest_framework import serializers
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin
from sm.product.gsc import zoho

from sm.product.gsc import models


class Error(Exception):
    pass


logger = logging.getLogger(__name__)


class UserSerializer(serializers.Serializer):
    granted = serializers.BooleanField()  # read_only
    registered = serializers.BooleanField()
    user_token = serializers.CharField()
    phone_number = serializers.CharField()
    reseller_id = serializers.IntegerField()
    reseller_name = serializers.CharField()
    contact_email = serializers.CharField()
    install_status = serializers.CharField()
    user_id = serializers.IntegerField()  # read_only
    email = serializers.CharField()
    source = serializers.CharField()
    name = serializers.CharField()
    not_granted_reason = serializers.CharField()
    google_id = serializers.CharField(required=False)
    install_type = serializers.CharField(required=False)


def parse_gauth_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "").split(" ", 1)
    if not auth or auth[0] != 'gauth' or len(auth) != 2 or not auth[1]:
        return None
    return auth[1]


def retrieve_google_oauth2_userinfo(access_token):
    url = 'https://www.googleapis.com/oauth2/v2/userinfo?access_token=' + access_token
    response = requests.get(url)
    if response.status_code >= 400:
        raise Error("access_token %s not valid" % access_token)

    return response.json()


def get_gsc_granted_status(email, registered=False, google_id=None, install_type=None):
    url = settings.GSC_PRODUCT_URL + '/api/install?email=' + email
    data = {"registered": registered}
    if google_id:
        data.update({'gmailUserId': google_id})
    if install_type:
        data.update({'installType': install_type})
    header = {"Authorization": "GSC-TOKEN " + settings.GSC_API_TOKEN, "Content-Type": "application/json"}
    logger.info("Ping gsc/api/install with registered: %s and google_id: %s", registered, google_id)
    response = requests.post(url, json=data, headers=header)

    user = models.User.objects.get(email__iexact=email)

    if settings.TEST_MODE and not (response.json().get('granted')):
        granted = models.get_gsc_test_granted_status(user.customer.name)

        logger.info("granted status for %s : %s", email, granted)
        if granted and settings.TEST_MODE:
            return {'granted': granted}
    return response.json()


def parse_user_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "").split(" ", 1)
    if not auth or auth[0] != 'user-token' or len(auth) != 2 or not auth[1]:
        return None
    return auth[1]


def get_user_with_token(token):
    """
    """
    token = Token.objects.filter(key=token).first()
    assert isinstance(token, Token)
    if token and (now() - token.created).total_seconds() < 3600 * 24:
        return token.user.sm

    return None


def get_user_token(user):
    """Retrieve token from rest authtoken

    When the token is older than 1 day, a new token will be created
    :rtype: unicode
    """
    token, created = Token.objects.get_or_create(
        user=user.auth_user
    )

    assert isinstance(token, Token)

    if (now() - token.created).total_seconds() > 3600 * 24:
        token.delete()
        token = Token.objects.create(
            user=user.auth_user
        )

    return token.key


def is_email_pure_gmail(email):
    return email.lower().endswith('googlemail.com') or email.lower().endswith('gmail.com')


def get_user_domain(email):
    if is_email_pure_gmail(email):
        domain = email.replace('@', "__")
    else:
        domain = email.rsplit('@', 1)[-1]
    return domain


class UserView(ViewSetMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        userinfo = self._get_user(request)
        email = userinfo.get('email')
        created = True
        source = self.request.data.get('source')
        if self._is_user_exists(email):
            user = self._update_user(email, userinfo)
            created = False
        else:
            user = self._create_user(userinfo, source=source)

        serializer = self.create_serializer(user)
        serializer.is_valid()
        zoho.create_lead(user, detect_account=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        logger.info("request data: %s, parsers: %s", request.data, request.parsers)
        user = self._get_user_by_token(request)
        if user is None:
            raise Http404("Not found")

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid()

        # added as per https://gappsexperts.atlassian.net/browse/GSC2017-254
        # returning also googleId that was sent in request if the user is a gmail user
        if is_email_pure_gmail(user.email) and 'google_id' in serializer.data:
            google_id = serializer.data['google_id']
        else:
            google_id = None

        if 'install_type' in serializer.data:
            install_type = serializer.data['install_type']
        else:
            install_type = None
        if request.data.get('registered') or request.data.get("check_granted"):
            granted = get_gsc_granted_status(email=user.email, registered=True,
                                             google_id=google_id,
                                             install_type=install_type)
        else:
            granted = None

        if granted and granted.get('granted') and not user.customer.registered:
            source = "GSC Install - Marketplace"
        else:
            source = None

        grant = False
        if granted and 'granted' in granted:
            grant = granted.get('granted')
        user = self._update_user(user.email, serializer, source=source, granted=grant)

        serializer = self.create_serializer(user, granted=granted)
        serializer.is_valid()

        # update lead
        zoho.create_lead(user, detect_account=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def install_state(self, request):
        if not settings.TEST_MODE:
            raise Http404("Not found")

        email = request.query_params.get('email')
        domain = get_user_domain(email)
        customer = models.Customer.objects.filter(name=domain).first()

        installed = False
        if customer:
            registered = customer.registered
            granted = get_gsc_granted_status(email, registered)
            if registered and granted['granted']:
                models.set_gsc_test_granted_status(domain)
                installed = True
        else:
            logger.warn("No domain found %s", domain)

        logger.info("install state for %s : %s", email, installed)
        return Response(dict(installed=installed))

    def _is_user_exists(self, email):
        return models.User.objects.filter(email__iexact=email).exists()

    def _get_user(self, request):

        token = parse_gauth_token(request)
        if not token:
            raise exceptions.PermissionDenied("Empty google auth token")

        userinfo = retrieve_google_oauth2_userinfo(access_token=token)
        return userinfo

    def _update_user(self, email, userinfo_or_serializer, source=None, granted=False):
        if isinstance(userinfo_or_serializer, UserSerializer):
            data = userinfo_or_serializer.data
        else:
            data = userinfo_or_serializer

        user = models.User.objects.get(email__iexact=email)
        customer = user.customer

        if 'phone_number' in data:
            user.phone_number = data['phone_number']

        if 'reseller_id' in data:
            if data['reseller_id'].isdigit():
                customer.reseller_id = int(data['reseller_id'])
                customer.reseller_name = ''
            else:
                customer.reseller_id = None
                customer.reseller_name = ''

        else:
            if 'reseller_name' in data:
                customer.reseller_name = data['reseller_name']

        prev_registered = customer.registered
        if not customer.registered:
            if 'registered' in data:
                customer.registered = str(data['registered']).lower() == 'true'
                models.GSCTestDomain.objects.update_or_create(dict(
                    registered=customer.registered
                ), domain=user.customer.name)
                logger.info("registered is set %s on %s in GSCTestDomain", customer.registered, user.customer.name)

        prev_install_status = customer.install_status
        if not prev_install_status:
            prev_install_status = ''

        granted = (
                granted or
                'granted' in prev_install_status.lower() or
                (source and 'marketplace' in source.lower()) or
                'granted' in data.get('install_status', '')
        )

        if settings.TEST_MODE and granted:
            models.set_gsc_test_granted_status(user.customer.name)

        if customer.registered:
            if not granted:
                if 'integrate' in data.get('install_status', ''):
                    customer.install_status = 'Registered+Integrateclicked'
                else:
                    customer.install_status = 'Registered'
            else:
                if not prev_registered:
                    customer.install_status = 'Granted+Registered'
                else:
                    customer.install_status = 'Registered+Granted'

        if 'contact_email' in data:
            user.contact_email = data['contact_email']
        if 'name' in data:
            user.name = data['name']
        if source:
            customer.source = source

        user.save()
        customer.save()
        return user

    def _create_user(self, userinfo, source=""):
        email = userinfo['email']
        assert isinstance(email, unicode)
        domain = get_user_domain(email)

        customer, created = models.Customer.objects.update_or_create(
            dict(
                name=domain,
                org_name=domain,
            ), name=domain
        )

        if created:
            customer.source = source
            customer.install_status = "signedIn"
            customer.save()
            logger.info("A new customer is created %s", customer)

        user = models.User.objects.create(
            customer=customer,
            name=userinfo.get('name', ''),
            email=userinfo['email'],
            contact_email=userinfo['email'],
        )

        logger.info("A new user is created %s", user)

        if settings.TEST_MODE:
            models.GSCTestDomain.objects.update_or_create(dict(domain=domain), domain=domain)
            logger.info("A new domain is created or updated in GSCTestDomain: %s", domain)

        return user

    def create_serializer(self, user, granted=None):
        user_token = get_user_token(user)
        customer = user.customer

        serializer_dict = {
            'registered': customer.registered,
            'user_token': user_token,
            'user_id': user.id,
            'phone_number': user.phone_number,
            'reseller_id': customer.reseller.id if customer.reseller else None,
            'reseller_name': customer.reseller.name if customer.reseller else customer.reseller_name,
            'contact_email': user.contact_email,
            'install_status': customer.install_status,
            'source': customer.source,
            'name': user.name,
            'email': user.email
        }

        if granted:
            serializer_dict.update({
                "granted": granted.get('granted', False),
                "not_granted_reason": granted.get('reason', '')
            })

        serializer_variables = UserSerializer(data=serializer_dict)
        return serializer_variables

    def _get_user_by_token(self, request):
        token = parse_user_token(request)
        if not token:
            raise exceptions.PermissionDenied("Empty user token")

        return get_user_with_token(token)
