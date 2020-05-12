from __future__ import absolute_import

from django.test import TestCase
from django.core import mail

from sm.product.gsc.mailer import send_mail_cancel_paypal_profile


class SendCancelEmailTest(TestCase):

    def test_send_cancel_profile_email(self):
        send_mail_cancel_paypal_profile('test.com', 'test-profile-id')
        self.assertEquals(len(mail.outbox), 1)
