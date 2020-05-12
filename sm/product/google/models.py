from __future__ import absolute_import

import logging

from django.utils.translation import ugettext_lazy as _
from django.db import models

from sm.core.models import Customer, Enum


logger = logging.getLogger(__name__)

PRODUCT_CLAZZ = 'GOOGLE'

RESELLER = 'reseller'


class OrderActionChoices(Enum):
    UPDATE = ('UPDATE', 'Update order')
    CREATE = ('CREATE', 'Create order')


class StatusType(Enum):
    ACTIVE = ('ACTIVE', _('Active'))
    BILLING_ACTIVATION_PENDING = ('BILLING_ACTIVATION_PENDING', _('Billing activation pending'))
    CANCELLED = ('CANCELLED', _('Cancelled'))
    PENDING = ('PENDING', _('Pending'))
    SUSPENDED = ('SUSPENDED', _('Suspended'))


class PlanName(Enum):
    ANNUAL_MONTHLY_PAY = ('ANNUAL', _('Annual monthly pay'))
    ANNUAL_YEARLY_PAY = ('ANNUAL_YEARLY_PAY', _('Annual yearly pay'))
    FLEXIBLE = ('FLEXIBLE', _('Flexible'))
    TRIAL = ('TRIAL', _('Trial'))
    FREE = ('FREE', _('Free'))


class RenewalType(Enum):
    AUTO_RENEW_MONTHLY_PAY = ('AUTO_RENEW_MONTHLY_PAY', _('Auto renew monthly pay'))
    AUTO_RENEW_YEARLY_PAY = ('AUTO_RENEW_YEARLY_PAY', _('Auto renew yearly pay'))
    CANCEL = ('CANCEL', _('Cancel'))
    RENEW_CURRENT_USERS_MONTHLY_PAY = ('RENEW_CURRENT_USERS_MONTHLY_PAY', _('Renew current users monthly pay'))
    RENEW_CURRENT_USERS_YEARLY_PAY = ('RENEW_CURRENT_USERS_YEARLY_PAY', _('Renew current users yearly pay'))
    SWITCH_TO_PAY_AS_YOU_GO = ('SWITCH_TO_PAY_AS_YOU_GO', _('Switch to pay as you go'))


class GoogleTransferToken(models.Model):
    token = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer)

    class Meta:
        db_table = 'gsuite_transfer_token'
