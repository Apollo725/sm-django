from __future__ import absolute_import

import json
from unittest import skip

import django.core.exceptions
import mock
import requests
import requests_mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import client
from rest_framework.test import APITestCase

from sm.product.gsc import models
from sm.product.gsc.api.apiview.users import UserView, UserSerializer
from sm.product.gsc.api.apiview.users import get_gsc_granted_status, retrieve_google_oauth2_userinfo, get_user_token


class UsersTest(APITestCase):

    GOOGLE_DATA = ('client_secret=dVt6xYg4yN4lApQ9FOMwcExB&grant_type=refresh_token&refresh_token='
                   '1%2FMOtKiQ33K95NucSdIQQqObx2lyD51McWdJXLsTgI0Xo&client_id=643378504561-o207o7hsp'
                   '1me1n3rru6mp9367k8agmdc.apps.googleusercontent.com')

    def setUp(self):
        self.factory = client.RequestFactory()
        self.UserView = UserView()

    @mock.patch('sm.product.gsc.api.apiview.users.retrieve_google_oauth2_userinfo')
    def test_get_user(self, mock_userinf):
        mock_userinf.return_value = dict(email='hoo@econsulting.fr')
        request = self.factory.post('', **{'HTTP_AUTHORIZATION': 'gauth 123456'})

        view = UserView()
        userinfo = view._get_user(request)

        self.assertEquals('hoo@econsulting.fr', userinfo.get('email'))
        self.assertRaises(django.core.exceptions.PermissionDenied, lambda: view._get_user(self.factory.post('')))

    @mock.patch('sm.product.gsc.api.apiview.users.retrieve_google_oauth2_userinfo')
    @mock.patch('sm.product.gsc.api.apiview.users.get_gsc_granted_status')
    @mock.patch('sm.product.gsc.api.apiview.users.UserView._update_user')
    @mock.patch('sm.product.gsc.api.apiview.users.UserView._create_user')
    @mock.patch('sm.product.gsc.api.apiview.users.UserView.create_serializer')
    def test_user_sign_in(self, create_serializer, _create_user, _update_user, get_gsc_granted_status, mock_userinfo):
        # Stubs
        domain = "econsulting.fr"
        email = 'hoo@econsulting.fr'

        customer = models.Customer.objects.create(name=domain)
        user = models.User.objects.create(email=email, customer=customer)

        mock_userinfo.return_value = dict(email=email)
        get_gsc_granted_status.return_value = True

        _update_user.return_value = user
        _create_user.return_value = user

        serializer = UserView.serializer_class(data=dict(contact_email=email, user_id=user.id))
        create_serializer.return_value = serializer
        # end Stubs

        response = self.client.post(reverse('api:gsc:user-sign-in'), **{'HTTP_AUTHORIZATION': 'gauth 123456'})
        response = json.loads(response.content)
        self.assertEqual(email, response.get('contactEmail'))
        self.assertEqual(user.id, response.get('userId'))

        mock_userinfo.return_value = dict(email="stef@econsulting.fr")
        self.client.post(reverse('api:gsc:user-sign-in'), **{'HTTP_AUTHORIZATION': 'gauth 123456'})
        self.assertTrue(_create_user.called)

    @mock.patch('sm.product.gsc.api.apiview.users.UserView._get_user_by_token')
    @mock.patch('sm.product.gsc.api.apiview.users.get_gsc_granted_status')
    @mock.patch('sm.product.gsc.api.apiview.users.UserView._update_user')
    @mock.patch('sm.product.gsc.api.apiview.users.UserView.create_serializer')
    def test_user_update(self, create_serializer, _update_user, get_gsc_granted_status, _get_user_by_token):
        # Stubs
        domain = "econsulting.fr"
        email = 'hoo@econsulting.fr'

        customer = models.Customer.objects.create(name=domain)
        user = models.User.objects.create(email=email, customer=customer)
        _get_user_by_token.return_value = user
        get_gsc_granted_status.return_value = True
        _update_user.return_value = user
        create_serializer.return_value = UserView.serializer_class(data=dict(contact_email=email, user_id=user.id))
        # end Stubs

        response = self.client.put(
            reverse("api:gsc:user-update"), **{'HTTP_AUTHORIZATION': 'user-token 123456'})

        response = json.loads(response.content)
        self.assertEqual(email, response.get('contactEmail'))
        self.assertEqual(user.id, response.get('userId'))

    # TODO(greg_eremeev) MEDIUM: need to use mock instead of http request
    @skip("have to be fixed")
    def test_retrieve_google_oauth2_userinfo(self):
        email = 'jevgenij@gappsexperts.com'
        url = 'https://www.googleapis.com/oauth2/v4/token'

        response = requests.post(url, data=self.GOOGLE_DATA,
                                 headers={'content-type': 'application/x-www-form-urlencoded'})
        # TODO(greg_eremeev) HIGH: need to clarify why google started to return 400 code
        response.raise_for_status()
        response_native = json.loads(response.text)
        response_data = retrieve_google_oauth2_userinfo(response_native['access_token'])
        self.assertEqual(email, response_data.get('email'))

    def test_get_gsc_granted_status(self):
        email = 'jevgenij@gappsexperts.com'
        # todo: this is currently not functional
        url = settings.GSC_PRODUCT_URL + '/api/install?email=' + email
        header = {'Authorization': 'GSC-TOKEN ' + settings.GSC_API_TOKEN}
        data = {'granted': True}
        request_data = json.dumps(data)

        with requests_mock.Mocker() as m:
            m.post(url, text=request_data, headers=header)
            self.assertEquals(data, get_gsc_granted_status(email, registered=True))

    @skip('need to fix this test')
    def test_create_serializer(self):
        domain = "gappsexperts.com"
        email = 'jevgenij@gappsexperts.com'

        customer = models.Customer.objects.create(name=domain)
        user = models.User.objects.create(email=email, customer=customer)

        granted = {'granted': True}
        serializer = self.UserView.create_serializer(user, granted)
        serializer.is_valid()

        self.assertEqual(email, serializer.data['contact_email'])
        user_token = get_user_token(user)
        self.assertEqual(user_token, serializer.data['user_token'])
        self.assertEqual(granted, serializer.data['granted'])
        self.assertEqual(customer.registered, serializer.data['registered'])
        self.assertEqual(user.id, serializer.data['user_id'])
        self.assertEqual(user.phone_number, serializer.data['phone_number'])
        self.assertEqual(customer.reseller_id, serializer.data['reseller_id'])
        self.assertEqual(customer.name, serializer.data['reseller_name'])
        self.assertEqual(customer.install_status, serializer.data['install_status'])

    # TODO(greg_eremeev) MEDIUM: need to use mock instead of http request
    @skip("have to be fixed")
    def test_create_user(self):
        email = 'jevgenij@gappsexperts.com'
        url = 'https://www.googleapis.com/oauth2/v4/token'

        response = requests.post(url, data=self.GOOGLE_DATA,
                                 headers={'content-type': 'application/x-www-form-urlencoded'})
        response.raise_for_status()
        response_native = json.loads(response.text)
        userinfo = retrieve_google_oauth2_userinfo(response_native['access_token'])
        test_userinfo = self.UserView._create_user(userinfo)

        customer = models.Customer.objects.get(name=userinfo.get('hd').lower())
        user = models.User.objects.get(email=email, customer=customer)

        # TODO(greg_eremeev) MEDIUM: need to clarify how customer.name is filled
        # self.assertEqual(customer.name, test_userinfo.name.lower())
        self.assertEqual(user.name, test_userinfo.name)
        self.assertEqual(user.email, test_userinfo.email)

    def test_update(self):
        name = 'jevgenij lezner'
        email = 'jevgenij@gappsexperts.com'
        userinfo_1 = {
            "granted": "true",
            "registered": "true",
            "user_token": "ad3fb9751d3ec93d6f436e4aaf8a5666a87dcc40",
            "phone_number": "860371733",
            "reseller_id": '1',
            "reseller_name": "jevgenij lezner",
            "contact_email": "jevgenij@gappsexperts.com",
            "install_status": 'Registered',
            "user_id": 1
        }

        userinfo_2 = {
            "granted": "true",
            "registered": "false",
            "user_token": "ad3fb9751d3ec93d6f436e4aaf8a5666a87dcc40",
            "phone_number": "867788955",
            "reseller_id": '1',
            "reseller_name": "jevgenij lezner",
            "contact_email": "jevgenij@gappsexperts.com",
            "install_status": 'Registered',
            "user_id": 1
        }

        customer = models.Customer.objects.create(name=name)
        user = models.User.objects.create(customer=customer, name=name, email=email)

        serializer = UserSerializer(data=userinfo_1)
        serializer.is_valid()
        test_userinfo = self.UserView._update_user(email, serializer)

        customer = models.Customer.objects.get(name=name)
        user = models.User.objects.get(email=email, customer=customer)

        self.assertEqual(customer.name, name)
        self.assertEqual(user.name, name)
        self.assertEqual(user.email, email)
        self.assertEqual(user.phone_number, userinfo_1['phone_number'])
        self.assertEqual(customer.name, userinfo_1['reseller_name'])
        self.assertEqual(customer.reseller_id, int(userinfo_1['reseller_id']))
        self.assertEqual(customer.install_status, userinfo_1['install_status'])
        self.assertEqual(customer.registered, True)

        test_userinfo = self.UserView._update_user(email, userinfo_2)

        customer = models.Customer.objects.get(name=name)
        user = models.User.objects.get(email=email, customer=customer)

        self.assertEqual(customer.name, name)
        self.assertEqual(user.name, name)
        self.assertEqual(user.email, email)
        self.assertEqual(user.phone_number, userinfo_2['phone_number'])
        self.assertEqual(customer.name, userinfo_2['reseller_name'])
        self.assertEqual(customer.reseller_id, int(userinfo_2['reseller_id']))
        self.assertEqual(customer.install_status, userinfo_2['install_status'])
        # TODO(greg_eremeev) MEDIUM: there is no way to make a change registered:true -> registered:false
        #                            via UserView._update_user
        # self.assertEqual(customer.registered, False)
