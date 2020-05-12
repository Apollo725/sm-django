from django.test import TestCase

from sm.core.models import BraintreePaymentMethod
from sm.product.gsc.models import save_payment_method
from sm.core.braintree_helper import get_payment_detail, save_payment_detail


class BraintreeTest(TestCase):

    TOKEN_PAYPAL = 'd22tfj'
    TOKEN_CREDIT_CARD = '586j8y'

    CREDIT_CARD_TYPE = 'credit_card'
    PAYPAL_TYPE = 'paypal'

    # TODO(greg_eremeev) MEDIUM: need to create mock instead of http request to BRAINTREE API
    def test_braintree(self):
        payment_credit_card = get_payment_detail(self.TOKEN_CREDIT_CARD)
        save_payment_method(payment_credit_card.customer_id, self.TOKEN_CREDIT_CARD)
        save_payment_detail(payment_credit_card)

        bpm_credit_card = BraintreePaymentMethod.objects.get(token=self.TOKEN_CREDIT_CARD)
        self.assert_credit_card(bpm_credit_card, payment_credit_card)

        payment_paypal = get_payment_detail(self.TOKEN_PAYPAL)
        save_payment_method(payment_paypal.customer_id, self.TOKEN_PAYPAL)
        save_payment_detail(payment_paypal)

        bpm_paypal = BraintreePaymentMethod.objects.get(token=self.TOKEN_PAYPAL)
        self.assert_paypal(bpm_paypal, payment_paypal)

    def assert_credit_card(self, bpm_credit_card, payment_credit_card):
        self.assertEquals(bpm_credit_card.last_4_digits, payment_credit_card.last_4)
        self.assertEquals(bpm_credit_card.expiration_date, payment_credit_card.expiration_date)
        self.assertEquals(bpm_credit_card.card_type, payment_credit_card.card_type)
        self.assertEquals(bpm_credit_card.type, self.CREDIT_CARD_TYPE)

    def assert_paypal(self, bpm_paypal, payment_paypal):
        self.assertEquals(bpm_paypal.email_address, payment_paypal.email)
        self.assertEquals(bpm_paypal.type, self.PAYPAL_TYPE)
