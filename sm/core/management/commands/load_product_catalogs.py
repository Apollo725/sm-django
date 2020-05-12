import logging
import csv

from django.core.management.base import BaseCommand

from sm.core.models import ProductCatalog


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Load product-catalog entries to update DB based on a csv file with a header" \
           " that complies with attribute names"

    def add_arguments(self, parser):
        parser.add_argument('--file_path', type=str)

    def handle(self, *args, **options):
        file_path = options['file_path']

        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            for row in csv_reader:
                line_count += 1
                try:
                    keys = dict({
                        'catalog_id': row['catalog_id'],
                        'product_id': row['product_id']
                    })
                    updates = dict({
                        'price': row['price'],
                        'per_user': row['per_user'] == 'TRUE',
                        'self_service': row['self_service'] == 'TRUE'
                    })
                except:
                    logger.error('Error loading row {}'.format(line_count))
                try:
                    ProductCatalog.objects.update_or_create(
                        defaults=updates,
                        **keys
                    )
                except:
                    logger.error('Error creating entry from row {}'.format(line_count))

            logger.info('Successfully created/updated {} rows'.format(line_count))
