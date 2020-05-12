from __future__ import absolute_import

import functools
import logging
import socket
import sys
import time
import traceback
import urllib
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET

import httplib2
import requests
import uritemplate
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.utils.decorators import available_attrs

import sm.core.models as core_models
import sm.test.models as test_models
from sm.product.gsc import models

logger = logging.getLogger(__name__)


# required packages:
# uritemplate >= 0.6

class Error(Exception):
    def __init__(self, code, message, cause=None):
        super(Error, self).__init__(message)
        self.code = int(code)

    def __str__(self):
        return "{}: {}".format(self.code, self.message)


class NotFoundError(Error):
    def __init__(self, code=4422, message="There is no data to show"):
        super(NotFoundError, self).__init__(code, message)


class ServiceError(Error):
    pass


class Record(dict):
    """A dict object represents an record in zoho crm

    key is the field name
    """
    module = None  # module name (Leads, Contacts, Accounts, etc...)
    id_field_name = None

    def __init__(self, *arg, **kwargs):
        super(Record, self).__init__(*arg, **kwargs)

    def __nonzero__(self):
        return True

    @classmethod
    def from_element(cls, element):
        """
        :type element: xml.etree.ElementTree.Element
        """
        record = cls()
        for field in element.iterfind("./FL"):
            record[field.attrib['val']] = field.text.strip() if field.text else ""

        return record

    def get_id(self):
        if 'Id' in self:
            return self['Id']
        if self.id_field_name in self:
            return self[self.id_field_name]
        return None

    def write(self, element):
        """
        :type element: xml.etree.ElementTree.Element
        """
        for key in self.keys():
            e = ET.Element('FL', {'val': key})
            e.text = unicode(self[key])
            element.append(e)

        return element

    def to_element(self):
        return self.write(ET.Element(self.module if self.module else self.__class__.__name__))

    @classmethod
    def wrap(cls, records):
        assert cls.module is not None
        element = ET.Element(cls.module)
        count = 0
        for record in records:
            count += 1
            row = ET.Element('row', {'no': str(count)})
            record.write(row)
            element.append(row)

        return element

    @classmethod
    def to_xml_string(cls, records):
        return ET.tostring(cls.wrap(records))


class Lead(Record):
    module = "Leads"
    id_field_name = "LEADID"


class Account(Record):
    module = "Accounts"
    id_field_name = "ACCOUNTID"


class Contact(Record):
    module = "Contacts"
    id_field_name = "CONTACTID"


class Potential(Record):
    module = "Potentials"
    id_field_name = "POTENTIALID"


class SalesOrder(Record):
    module = "SalesOrders"
    id_field_name = "SALESORDERID"


class ConvertLeadOption(Record):
    def write(self, element):
        """
        :type element: xml.etree.ElementTree.Element
        """
        for key in self.keys():
            e = ET.Element('option', {'val': key})
            e.text = self[key]
            element.append(e)

        return element


class ConvertLeadResult(object):
    def __init__(self, contact_id, account_id, potential_id=None):
        self.contact_id = contact_id
        self.account_id = account_id
        self.potential_id = potential_id

    @classmethod
    def parse(cls, element):
        """
        :type element: xml.etree.ElementTree.Element
        """
        result = cls(
            element.find('./Contact').text,
            element.find('./Account').text,
        )

        potential = element.find('./Potential')
        if potential is not None:
            result.potential_id = potential.text

        return result


class Fields(object):
    class Section(dict):
        def __init__(self, fields=None, **kwargs):
            super(Fields.Section, self).__init__(**kwargs)
            self.fields = [] if fields is None else fields

    class Field(dict):
        pass

    def __init__(self, sections=None, fields=None):
        self.sections = [] if sections is None else sections
        self.fields = [] if fields is None else fields

    @classmethod
    def parse(cls, element):
        """

        :type element: xml.etree.ElementTree.Element
        """
        fields = Fields()
        for section_element in element.iterfind("./section"):
            section = cls.Section()
            section.update(section_element.attrib)
            for field_element in section_element.iterfind('./FL'):
                field = cls.Field()
                field.update(field_element.attrib)
                section.fields.append(field)
            fields.sections.append(section)

        for field_element in element.iterfind("./FL"):
            field = cls.Field()
            field.update(field_element.attrib)
            fields.fields.append(field)

        return fields


class PostResult(object):
    def __init__(self, message, detail, error=False):
        """
        :type detail: PostResult.Detail
        :type message: str
        :type error: bool
        """
        self.message = message
        self.detail = detail
        self.error = error

    class Detail(Record):
        pass


def retry(func=None, max_retries=1):
    def decorator(method):
        @functools.wraps(method, assigned=available_attrs(method))
        def retry_func(*args, **kwargs):
            def retries(remaining, *args, **kwargs):
                try:
                    return method(*args, **kwargs)
                except socket.error as e:
                    if remaining > 0:
                        remaining -= 1
                        sleep = 0.5 * (2 ** (max_retries - remaining))
                        if not settings.TESTING:
                            logger.warn("network error happens, retrying %s after %d seconds ..., %s", method, sleep, e)
                            traceback.print_exc(file=sys.stderr)
                        time.sleep(sleep)
                        return retries(remaining, *args, **kwargs)
                    else:
                        raise e

            return retries(max_retries, *args, **kwargs)

        return retry_func

    if func:
        return decorator(func)
    else:
        return decorator


# noinspection PyProtectedMember
class Client(object):
    new_format = 1
    version = 1
    scope = 'crmapi'

    def __init__(self, token=None, api_server_url=None, using_requests=False):
        self.token = token
        self.session = requests.Session()
        self.use_requests = using_requests
        self.api_server_url = ('https://crm.zoho.com'
                               if not api_server_url else api_server_url)

    @property
    def http(self):
        return httplib2.Http(timeout=10)

    def set_new_format(self, new_format):
        self.new_format = new_format

    @property
    def template(self):
        return self.api_server_url + "/crm/private/xml{/path*}"

    def build_uri(self, path):
        context = {'domain': 'crm.zoho.com', 'scope': 'crm', 'format': 'xml', 'path': path}

        return uritemplate.expand(self.template, context)

    def update_default_params(self, params):
        if self.token:
            if 'authtoken' not in params:
                params['authtoken'] = self.token

        if 'version' not in params:
            params['version'] = self.version

        if 'newFormat' not in params:
            params['newFormat'] = self.new_format

        if 'scope' not in params:
            params['scope'] = self.scope

    def parse_response(self, response):
        """

        :rtype : xml.etree.ElementTree.Element
        """
        if not self.use_requests:
            response, content = response
            if int(response.status) != 200:
                raise Error(int(response.status), content)
        else:
            content = response.text.encode('utf8')
            if int(response.status_code) != 200:
                raise Error(response.status_code, content)

        try:
            et = ET.fromstring(content)
        except ET.ParseError as e:
            raise Error(500, e.message)

        no_data = et.find('./nodata')
        if no_data is not None:
            raise NotFoundError(no_data.find('code').text, no_data.find('message').text)

        error = et.find('./error')
        if error is not None:
            raise ServiceError(error.find('code').text, error.find('message').text)

        return et

    @retry(max_retries=3)
    def get(self, uri, params=None):
        if params is None:
            params = {}
        self.update_default_params(params)
        if not self.use_requests:
            response = self.http.request(uri + "?" + urllib.urlencode(params))
        else:
            response = self.session.get(uri, params=params)
        return self.parse_response(response)

    @retry(max_retries=3)
    def post(self, uri, data):
        """
        :rtype : xml.etree.ElementTree.Element
        """
        self.update_default_params(data)
        if not self.use_requests:
            response = self.http.request(uri + "?" + urllib.urlencode(data))
        else:
            response = self.session.post(uri, data)
        return self.parse_response(response)

    def search_records(self, record_class, criteria, from_index=1, to_index=20, select_columns=None):
        """Get the list of records that meet your search criteria

        see https://www.zoho.com/crm/help/api/searchrecords.html

        sample url:
        https://crm.zoho.com/crm/private/xml/Leads/searchRecords?authtoken=Auth Token&scope=crmapi&criteria=(Company:xx)

        :param record_class:  The class of record
        :type record_class: Type[Record]
        :param criteria: The search criteria
        :param from_index:
        :param to_index:
        :param select_columns:
        :rtype : Record
        :raises : NotFoundError, ServiceError
        """
        params = {
            'criteria': criteria,
            'fromIndex': from_index,
            'toIndex': to_index
        }

        if select_columns:
            params['selectColumns'] = select_columns

        logger.debug("search %s with criteria %s", record_class.__name__, criteria)
        try:
            response = self.get(self.build_uri([record_class.module, "searchRecords"]), params)
        except NotFoundError:
            return []
        return [record_class.from_element(element) for element in
                response.iterfind('./result/{}/row'.format(record_class.module))]

    @staticmethod
    def dict_from_list(record):
        """Get dictionary from list object.
        ex: [{'a'=>'b'}] => {'a' => 'b'}

        :type record: type(List)
        :param record: result of converting dictionary
        :rtype : dictionary
        :raises :
        """
        if len(record) > 0:
            return record[0]
        else:
            return {}

    @staticmethod
    def get_format_record(record, model, rid):
        """Format model fields type to real crm fields type
        ex: Lead['gsc_status'] -> Lead['GSC Status']

        :type record: type(Dictionary)
        :type model: type(Model)
        :type rid: type(int)
        :param record: result of converting dictionary
        :param model: Model instance for fake crm.
        :param rid: result of converting dictionary
        :rtype : dictionary
        :raises :
        """

        records = Client.dict_from_list(model.objects.filter(id=rid).values())

        for field in model._meta.get_fields():
            if str(field.attname) in records:
                record[str(field._verbose_name)] = (list(records.values())[list(records.keys()).index(field.attname)])
        return record

    @staticmethod
    def create_zoho_record(model, record):
        """Format real crm fields with model fields type
        ex: Lead['GSC Status'] -> Lead['gsc_status']

        :type model: type(Model Instance)
        :type record: type(Dictionary)
        :param model: model instance for zoho
        :param record: object which need to be converted
        :rtype : PostResult
        :raises :
        """

        result = {}
        for field in model._meta.get_fields():
            if field._verbose_name is not None and str(field._verbose_name) in record:
                result[str(field.attname)] = (list(record.values())[list(record.keys()).index(field._verbose_name)])

        if 'id' in result:
            result, _ = model.objects.update_or_create(defaults=result, id=result['id'])
        else:
            result = model.objects.create(**result)
        return PostResult("Record(s) added successfully", PostResult.Detail(Record({'Id': result.id})))

    @staticmethod
    def create_contact_from_lead_by_mock(record):
        """Create account from lead on model (test mode)

        :type record: type(Dictionary)
        :param record: lead object
        :rtype : id potential which is just created
        :raises :
        """
        records = {}
        for lead in record.keys():
            for potential in test_models.MockZohoContact._meta.get_fields():
                if lead is not None and lead == potential.attname and lead != 'id':
                    records[str(potential.attname)] = (list(record.values())[list(record.keys()).index(lead)])

        contact, _ = test_models.MockZohoContact.objects.update_or_create(**records)
        return contact.id

    @staticmethod
    def create_account_from_lead_by_mock(record):
        """Create account from lead on model (test mode)

        :type record: type(Dictionary)
        :param record: lead object
        :rtype : id potential which is just created
        :raises :
        """
        data_dict = {}
        for lead in record.keys():
            for potential in test_models.MockZohoAccount._meta.get_fields():
                if lead == potential.attname and lead != 'id' and lead is not None:
                    data_dict[str(potential.attname)] = (list(record.values())[list(record.keys()).index(lead)])

        account, _ = test_models.MockZohoAccount.objects.update_or_create(**data_dict)
        return account.id

    @staticmethod
    def create_potential_from_lead_by_mock(record, potential_dict):
        """Create potential from lead on model (test mode)

        :type record: type(Dictionary)
        :type potential_dict: type(Dictionary)
        :param record: lead object
        :param potential_dict: potential object
        :rtype : id potential which is just created
        :raises :
        """

        new_record = {}
        for potential in test_models.MockZohoPotential._meta.get_fields():
            potential_name = potential.attname
            if potential_name != 'id' and potential_name in record:
                new_record[potential_name] = record[potential_name]
            elif potential_name in potential_dict:
                new_record[potential_name] = potential_dict[potential_name]

        potential, _ = test_models.MockZohoPotential.objects.update_or_create(**new_record)
        return potential.id

    def get_record_by_id(self, record_class, rid):
        """Retrieve individual records by record ID on zoho or fake zoho model depends on test setting.

        see https://www.zoho.com/crm/help/api/getrecordbyid.html

        :type record_class: type(Record)
        :param record_class:  The class of record
        :param rid: The id of record
        :rtype : Record
        :raises : NotFoundError
        """

        if settings.TEST_MODE:
            record = record_class()

            # On here, the model data will be formatted with zoho crm style, ex: ['gsc_status'] => ['GSC Status']
            if record_class.module == 'Leads':
                return self.get_format_record(record, test_models.MockZohoLead, rid)
            if record_class.module == 'Accounts':
                return self.get_format_record(record, test_models.MockZohoAccount, rid)
            if record_class.module == 'Contacts':
                return self.get_format_record(record, test_models.MockZohoContact, rid)
            if record_class.module == 'Potentials':
                return self.get_format_record(record, test_models.MockZohoPotential, rid)
            if record_class.module == 'SalesOrders':
                return self.get_format_record(record, test_models.MockZohoSalesOrder, rid)

        params = {'id': rid}
        logger.debug("getting record %s by id %s", record_class.__name__, rid)
        response = self.get(self.build_uri([record_class.module, 'getRecordById']), params)
        results = [record_class.from_element(element) for element in
                   response.iterfind('./result/{}/row'.format(record_class.module))]

        return results[0]

    def get_records_by_idlist(self, record_class, id_list):
        """Retrieve individual records by record ID

        see https://www.zoho.com/crm/help/api/getrecordbyid.html

        :type record_class: type(Record)
        :param record_class:  The class of record
        :param id_list: The id of record
        :rtype : dict
        :raises :ServiceError
        """
        assert len(id_list) <= 100, "number of id_list should never over 100"
        params = {'idlist': ";".join(id_list), "version": "2"}

        logger.debug("getting record %s by id_list %s and more...", record_class.__name__, id_list[:3])
        response = self.get(self.build_uri([record_class.module, 'getRecordById']), params)
        results = [record_class.from_element(element) for element in
                   response.iterfind('./result/{}/row'.format(record_class.module))]
        return dict(zip([result.get_id() for result in results], results))

    def update_record(self, record, trigger=True):
        """Update or modify the record in Zoho CRM or fake Zoho Model (only for test mode)

        :type record: Record
        :rtype : PostResult
        :param record: The record to update
        :param trigger: If to trigger
        """

        if settings.TEST_MODE:
            if record.module == 'Leads':
                return self.create_zoho_record(test_models.MockZohoLead, record)
            if record.module == 'Accounts':
                return self.create_zoho_record(test_models.MockZohoAccount, record)
            if record.module == 'Contacts':
                return self.create_zoho_record(test_models.MockZohoContact, record)
            if record.module == 'Potentials':
                return self.create_zoho_record(test_models.MockZohoPotential, record)
            if record.module == 'SalesOrders':
                return self.create_zoho_record(test_models.MockZohoSalesOrder, record)

        data = {
            'id': record.get_id(),
            'xmlData': record.to_xml_string([record])
        }

        if trigger:
            data['wfTrigger'] = 'true'

        logger.debug("updating %s %s", record.__class__, record)
        et = self.post(self.build_uri([record.module, 'updateRecords']), data)
        return PostResult(et.find("./result/message").text,
                          PostResult.Detail.from_element(et.find('./result/recorddetail')))

    def update_records(self, records, trigger=False):
        """Update or modify the records in Zoho CRM


        :type records: list
        :rtype : PostResult
        :param records: The records to update
        :param trigger: If to trigger
        """

        mapping = {}
        count = 0

        for record in records:
            assert record.get(record.id_field_name), record.id_field_name + " must not be null"
            count += 1
            record["Id"] = record[record.id_field_name]
            mapping[count] = record["Id"]

        assert len(records) <= 100, "Max size of records is 100"

        record = records[0]

        data = {
            'version': 4,
            'xmlData': record.to_xml_string(records),
        }

        if trigger:
            data['wfTrigger'] = 'true'

        logger.debug("updating multiple %s", record.__class__)

        et = self.post(self.build_uri([record.module, 'updateRecords']), data)

        def parse_row(_et):
            if _et.find('./error') is not None:
                return PostResult(
                    _et.find('./error/code').text,
                    _et.find('./error/details').text,
                    error=True
                )
            else:
                return PostResult(
                    _et.find('./success/code').text,
                    PostResult.Detail.from_element(_et.find('./success/details'))
                )

        return dict([(mapping[int(element.attrib['no'])],
                      parse_row(element)) for element in et.iterfind("./result/row")])

    def get_fields(self, module):
        """To retrieve details of fields available in a module

        :type module: Record or str
        """

        module = module if isinstance(module, basestring) else module.module
        return Fields.parse(self.get(self.build_uri([module, 'getFields'])))

    def create_sales_order(self, order):
        sales_order = SalesOrder()
        order_detail = order.details.first()
        product = order_detail.product
        catalog = order_detail.catalog
        product_catalog = core_models.ProductCatalog.objects.filter(product=product, catalog=catalog).first()
        customer = order.customer

        try:
            zoho_customer_record = customer.zohocustomerrecord
        except core_models.Customer.zohocustomerrecord.RelatedObjectDoesNotExist:
            return False, PostResult.Detail(Record())

        if zoho_customer_record.potential_id:
            potential_name = self.get_potential(zoho_customer_record.potential_id)['Potential Name']
        else:
            potential_name = ''

        if hasattr(customer, 'communication_user') and customer.communication_user:
            user = customer.communication_user
        else:
            user = customer.users.first()

        # TODO(greg_eremeev) LOW: 50 - maximum limit
        sales_order['Subject'] = order.name[:50]
        sales_order['First Name'] = user.first_name
        sales_order['Potential Name'] = potential_name
        if 'Account Name' in self.get_account(zoho_customer_record.account_id):
            sales_order['Account Name'] = self.get_account(zoho_customer_record.account_id)['Account Name']
        sales_order['Product'] = product.name
        sales_order['Quantity'] = order_detail.amount
        sales_order['Unit Price'] = product_catalog.price
        sales_order['Email'] = user.contact_email or user.email
        sales_order['TOTAL Price'] = order.total

        vendor_profile = models.try_to_get_vendor_profile(user.customer)
        # Added by Ans against ticket SM-153
        if vendor_profile:
            sales_order['Number Of Accounts'] = vendor_profile.users
            sales_order['Gapps Version'] = vendor_profile.apps_version
        else:
            sales_order['Number Of Accounts'] = ""
            sales_order['Gapps Version'] = ""

        sales_order['SM Order ID'] = order.id

        response = self.insert_record(sales_order, wf_trigger=True)
        if 'Record(s) added successfully' in response.message:
            success = True
        else:
            success = False
        return success, response.detail

    def get_account(self, _id):
        return self.get_record_by_id(Account, _id)

    def get_potential(self, _id):
        return self.get_record_by_id(Potential, _id)

    def insert_record(self, record, wf_trigger=False, duplicate_check=None):
        """Update or modify the record in Zoho CRM and fake Zoho Model (only on test mode)


        :param record: The record to update
        :type record: Record
        :param wf_trigger:
        :param duplicate_check: valid values is 1 (skip to update when duplicated found), 2 (update the existing record)
        :type duplicate_check: str
        :rtype : PostResult
        """

        if settings.TEST_MODE:
            if record.module == 'Leads':
                return self.create_zoho_record(test_models.MockZohoLead, record)
            if record.module == 'Accounts':
                return self.create_zoho_record(test_models.MockZohoAccount, record)
            if record.module == 'Contacts':
                return self.create_zoho_record(test_models.MockZohoContact, record)
            if record.module == 'Potentials':
                return self.create_zoho_record(test_models.MockZohoPotential, record)
            if record.module == 'SalesOrders':
                return self.create_zoho_record(test_models.MockZohoSalesOrder, record)

        data = {
            'xmlData': record.to_xml_string([record]),
            'wfTrigger': 'true' if wf_trigger else 'false',
        }

        if duplicate_check:
            data['duplicateCheck'] = duplicate_check

        logger.debug("inserting %s %s", record.__class__, record)
        et = self.post(self.build_uri([record.module, 'insertRecords']), data)
        return PostResult(et.find("./result/message").text,
                          PostResult.Detail.from_element(et.find('./result/recorddetail')))

    def convert_lead(self, lead_id, option, potential=None):
        records = [option]

        if potential:
            option['createPotential'] = 'true'
            records.append(potential)
        else:
            option['createPotential'] = 'false'

        data = {
            'xmlData': Potential.to_xml_string(records),
            'leadId': lead_id
        }

        logger.debug("converting lead %s %s %s", lead_id, option, potential)
        return ConvertLeadResult.parse(
            self.post(self.build_uri(['Leads', 'convertLead']), data=data)
        )

    def convert_lead_by_mock(self, lead_id, potential=None):
        """Convert a lead in fake zoho model.

        :type lead_id: id number
        :type potential: dict
        :rtype : ConvertLeadResult
        :param lead_id: id of lead object
        :param potential: potential data if exist
        """

        record = self.dict_from_list(test_models.MockZohoLead.objects.filter(id=lead_id).values())
        potential_id = 0

        if potential:
            potential_id = self.create_potential_from_lead_by_mock(record, potential)

        account_id = self.create_account_from_lead_by_mock(record)
        contact_id = self.create_contact_from_lead_by_mock(record)

        logger.debug("converting lead on fake mode %s %s", lead_id, potential)
        return ConvertLeadResult(contact_id, account_id, potential_id)


executor = ThreadPoolExecutor(max_workers=10)
