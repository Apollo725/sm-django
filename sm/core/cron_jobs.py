from django_cron import CronJobBase, Schedule
from django.core.management import call_command

from django.conf import settings


class CreateSalesOrdersCronJob(CronJobBase):

    RUN_AT_TIMES = [settings.RUN_SALES_ORDERS_CRON_JOB_AT_TIME]
    RUN_EVERY_MINS = 10

    code = 'sm.core.cron_jobs.CreateSalesOrdersCronJob'
    # schedule = Schedule(run_at_times=RUN_AT_TIMES)
    schedule = Schedule(run_every_mins=settings.SALES_ORDERS_RUN_EVERY_MIN)
    def do(self):
        # TODO(greg_eremeev) MEDIUM: need to use command object instead of command name
        # call_command('create_sales_orders', time_range_hours=settings.SALES_ORDERS_CRON_JOB_TIME_RANGE_HOURS)
        call_command('create_sales_orders', time_range_minutes=settings.SALES_ORDERS_RUN_EVERY_MIN)
