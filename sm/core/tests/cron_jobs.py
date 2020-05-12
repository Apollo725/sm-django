from decimal import Decimal

import mock
from django.test import TransactionTestCase
from django.core.management import call_command

from sm.core.models import OrderStatus
from sm.core.factories import SubscriptionFactory


class CreateSalesOrdersTest(TransactionTestCase):

    def setUp(self):
        def get_potential(*args, **kwargs):
            return {'Potential Name': 'potential_name'}

        def get_account(*args, **kwargs):
            return {'Account Name': 'account_name'}

        self.sales_order = {
            'Product': u'GSC professional version (flex prepaid)',
            'First Name': u'Greg', 'Unit Price': Decimal('0.00'),
            'Potential Name': 'potential_name', 'Account Name': 'account_name',
            'Subject': u'Gsc for greg.econsulting.fr (new subscription)',
            'Email': u'greg@greg.econsulting.fr', 'TOTAL Price': Decimal('20.0000'), 'Quantity': 50}

        self.mock_objects = []
        self.mock_objects.append(mock.patch('zoho_api.Client.get_potential', get_potential))
        self.mock_objects.append(mock.patch('zoho_api.Client.get_account', get_account))
        insert_record_mock = mock.patch('zoho_api.Client.insert_record')
        insert_record = insert_record_mock.start()
        for mock_obj in self.mock_objects:
            mock_obj.start()
        self.mock_objects.append(insert_record_mock)

        return_mock = mock.MagicMock()
        return_mock.message = 'Record(s) added successfully'
        return_mock.detail = 'detail'
        insert_record.return_value = return_mock
        self.insert_record = insert_record

    def tearDown(self):
        for mock_obj in self.mock_objects:
            mock_obj.stop()

    def test_create_sales_orders_one_opened_order(self):
        SubscriptionFactory()
        call_command('runcrons', 'sm.core.cron_jobs.CreateSalesOrdersCronJob', force=True)
        self.insert_record.assert_called_once_with(self.sales_order, wf_trigger=True)

    def test_create_sales_orders_paid_and_opened_order(self):
        subscription = SubscriptionFactory(order__status=OrderStatus.PAID)
        SubscriptionFactory(catalog=subscription.catalog, customer=subscription.customer,
                            product=subscription.product, order__status=OrderStatus.CREATED)
        call_command('runcrons', 'sm.core.cron_jobs.CreateSalesOrdersCronJob', force=True)
        self.insert_record.assert_not_called()
