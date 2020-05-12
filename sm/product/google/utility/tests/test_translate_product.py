from django.test import SimpleTestCase
from unittest import skip
# from ...utility.subscriptions_utility import _translate_product as translate_product

# from sm.product.google.models import PlanName as GooglePlanName


# class TestStringMethods(SimpleTestCase):
#     @skip("tests not existing function")
#     def test_translate_product(self):
#         self.assertEqual(translate_product('Google-Apps-For-Business', GooglePlanName.ANNUAL_MONTHLY_PAY),
#                          'GSUITE_BASIC_ANNUAL_MONTHLY')
#         self.assertEqual(translate_product('Google-Apps-For-Business', GooglePlanName.ANNUAL_YEARLY_PAY),
#                          'GSUITE_BASIC_ANNUAL_YEARLY')
#         self.assertEqual(translate_product('Google-Apps-For-Business', GooglePlanName.FLEXIBLE),
#                          'GSUITE_BASIC_FLEXIBLE')
#         self.assertEqual(translate_product('Google-Apps-For-Business', None), 'GSUITE_BASIC_UNKNOWN_PLAN')
#
#         self.assertEqual(translate_product('Google-Apps-Unlimited', GooglePlanName.ANNUAL_MONTHLY_PAY),
#                          'GSUITE_BUSINESS_ANNUAL_MONTHLY')
#         self.assertEqual(translate_product('Google-Apps-Unlimited', GooglePlanName.ANNUAL_YEARLY_PAY),
#                          'GSUITE_BUSINESS_ANNUAL_YEARLY')
#         self.assertEqual(translate_product('Google-Apps-Unlimited', GooglePlanName.FLEXIBLE),
#                          'GSUITE_BUSINESS_FLEXIBLE')
#         self.assertEqual(translate_product('Google-Apps-Unlimited', None), 'GSUITE_BUSINESS_UNKNOWN_PLAN')
#
#         self.assertEqual(translate_product('1010020020', GooglePlanName.ANNUAL_MONTHLY_PAY),
#                          'GSUITE_ENTERPRISE_ANNUAL_MONTHLY')
#         self.assertEqual(translate_product('1010020020', GooglePlanName.ANNUAL_YEARLY_PAY),
#                          'GSUITE_ENTERPRISE_ANNUAL_YEARLY')
#         self.assertEqual(translate_product('1010020020', GooglePlanName.FLEXIBLE), 'GSUITE_ENTERPRISE_FLEXIBLE')
#         self.assertEqual(translate_product('1010020020', None), 'GSUITE_ENTERPRISE_UNKNOWN_PLAN')
#         pass
