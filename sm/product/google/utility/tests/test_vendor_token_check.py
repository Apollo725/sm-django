# from __future__ import absolute_import
#
# import logging
#
# from django.core.urlresolvers import reverse
# from rest_framework.test import APITestCase
# from django.utils import timezone
#
# from sm.core.models import (AuthUser, User, Customer, VendorProfile, VendorProfileClazz)
# from sm.product.google import models
#
#
# logger = logging.getLogger(__name__)
#
#
# class VendorTokenCheckTests(APITestCase):
#     CUSTOMER_NAME = 'foo.com'
#
#     def setUp(self):
#         print ('Test starting')
#         customer = Customer.objects.create(name=self.CUSTOMER_NAME)
#         user = AuthUser.objects.create_superuser(username='test', email='test@foo.com', password='test')
#         sm_user = User.objects.create(name='test', customer=customer)
#         sm_user.auth_user = user
#         sm_user.save()
#         vendor_profile = VendorProfile.objects.create(name='test name', customer=customer)
#         VendorProfileClazz.objects.create(vendor_profile=vendor_profile, product_clazz='GSC')
#         gp = models.GoogleProduct.objects.create(product_name="Gsuite")
#         time_now = timezone.now()
#         models.GoogleSubscription.objects.create(product=gp, expiry_date=time_now)
#
#         self.assertEquals(user.sm.customer.name, 'foo.com')
#         self.client.defaults['HTTP_AUTHORIZATION'] = 'Token {}'.format(user.auth_token.key)
#         self.client.login(username='test', password='test')
#
#     def test_get_subscription(self):
#         sm_user_no = User.objects.count()
#         print (sm_user_no)
#         sm_user = User.objects.get(pk=1)
#         print(sm_user.name)
#         if sm_user.auth_user:
#             print(sm_user.auth_user.email)
#         print(AuthUser.objects.count())
#
#         response = self.client.post(reverse('google:check_vendor_token'),
#                                     data={'transfer_token': 'ABCD123'})
#         print(response.body)
#         print("test started | logs printing successfully")
#         logger.info("test started | logs printing successfully by logger")
#         self.assertEquals(200, response.status_code)
#         # self.assertTrue("detail" in response.content and "Not found" in response.content)
