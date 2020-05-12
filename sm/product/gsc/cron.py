from __future__ import absolute_import

import logging
import os.path

from django_cron import CronJobBase, Schedule
from . import renewer
from django.utils import timezone
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger(__name__)


class RenewCustomers(CronJobBase):
    RUN_AT_TIMES = ['04:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'sm.product.gsc.cron.renew_customers'

    # noinspection PyBroadException
    def do(self):
        try:
            subject = "Renewal summary of subscription manager %s" % timezone.now().strftime("%Y-%m-%d")
            errors, renews = renewer.renew()
            expires = renewer.expire_subscriptions()
            if errors or renews or expires:
                with open(os.path.join(os.path.dirname(__file__), 'email_templates', 'renew_report.html')) as template:
                    message = Template(template.read()).render(Context({
                        'renew_errors': errors,
                        'renew_renews': renews,
                        'expires': expires
                    }))
                    send_mail(
                        subject=subject,
                        message=subject,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email.strip() for email in settings.RENEW_REPORT_RECEIVER.split(',')]
                        ,
                        html_message=message
                    )
        except:
            logger.error("Cron failed to renew, exited with exception", exc_info=1)
