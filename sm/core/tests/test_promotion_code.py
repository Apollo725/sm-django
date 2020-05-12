import re

from django.test import TestCase

from sm.core.promotion import validate_code, Error


class PromotionTest(TestCase):

    fixtures = ['core/discount_codes']

    CODE = '7152214'
    DATES = {'correct': '010150', 'expired': '010170', 'invalid': '011370'}

    @staticmethod
    def gen_code(_code, date):
        return (_code[0] + date[0] + date[1] + _code[1] + _code[2] + date[4] + _code[3] + date[5] + _code[4]
                + date[2] + _code[5] + date[3] + _code[6])

    def test_validate_code(self):
        self.assertEquals(self.CODE, validate_code(self.gen_code(self.CODE, self.DATES['correct'])).code)
        self.assertRaisesRegexp(
            Error, re.compile('expired'),
            lambda: validate_code(self.gen_code(self.CODE, self.DATES['expired'])))

        self.assertRaisesRegexp(
            Error, re.compile('invalid date'),
            lambda: validate_code(self.gen_code(self.CODE, self.DATES['invalid'])))

        self.assertRaisesRegexp(
            Error, re.compile('not found'),
            lambda: validate_code(self.gen_code('1234567', self.DATES['correct'])))
