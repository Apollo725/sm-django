import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand

from zoho_api import Client
from sm.core.models import Order, OrderStatus


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Create sales orders in ZOHO CRM for orders which were not paid for the last N hours'

    def add_arguments(self, parser):
        # parser.add_argument('--time_range_hours', type=int)
        parser.add_argument('--time_range_minutes', type=int)

    def handle(self, *args, **options):
        client = Client(token=settings.ZOHO_API_TOKEN)
        time_range = timezone.now() - timedelta(minutes=options['time_range_minutes'])
        for order in Order.objects.filter(status=OrderStatus.CREATED, date__gte=time_range).all():
            customer = order.customer
            if Order.objects.filter(customer=customer, status=OrderStatus.PAID, date__gte=time_range).count() == 0:
                order_id = order.id
                try:
                    success, detail = client.create_sales_order(order)
                    if success:
                        logger.info('Sales order for order {} was created, detail: {}'.format(order_id, detail))
                    else:
                        logger.error('Sales order for order {} was not created, detail: {}'.format(order_id, detail))
                except:
                    logger.exception('Sales order was not created, order id: {}'.format(order.id), exc_info=True)
