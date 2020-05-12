from __future__ import absolute_import
from unittest import TestCase
import requests_mock
from django.utils.decorators import method_decorator
from zoho_api import *
import mock


class ClientTestCase(TestCase):
    def setUp(self):
        self.client = Client(using_requests=True)

    @requests_mock.mock()
    def test_search_records_not_found(self, m):
        # test not found
        m.get('https://crm.zoho.com/crm/private/xml/Leads/searchRecords',
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/searchRecords">
    <nodata>
        <code>4422</code>
        <message>There is no data to show</message>
    </nodata>
</response>''')

        results = self.client.search_records(Lead, '(Company:acacia.com)')
        self.assertEqual(len(results), 0)

    @requests_mock.mock()
    def test_search_records_invalid_field(self, m):
        m.get('https://crm.zoho.com/crm/private/xml/Leads/searchRecords',
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/searchRecords">
    <error>
        <code>4832</code>
        <message>API call cannot be completed as the Criteria parameter contains empty field name</message>
    </error>
</response>''')

        try:
            self.client.search_records(Lead, '(Company:acacia.com)')
        except ServiceError, e:
            self.assertEqual(e.code, 4832)
            return
        self.assertFalse(True)

    @requests_mock.mock()
    def test_search_records(self, m):
        # test found 2
        m.get('https://crm.zoho.com/crm/private/xml/Leads/searchRecords',
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/searchRecords">
    <result>
        <Leads>
            <row no="1">
                <FL val="LEADID">1144270000000431333</FL>
                <FL val="SMOWNERID">1144270000003086136</FL>
                <FL val="Lead Owner">
                    <![CDATA[Khedija Ben Attaya]]>
                </FL>
                <FL val="Company">
                    <![CDATA[gsc.alti.mobi]]>
                </FL>
            </row>
            <row no="2">
                <FL val="LEADID">1144270000000431333</FL>
                <FL val="SMOWNERID">1144270000003086136</FL>
                <FL val="Lead Owner">
                    <![CDATA[Khedija Ben Attaya]]>
                </FL>
                <FL val="Company">
                    <![CDATA[gsc.alti.mobi]]>
                </FL>
            </row>
        </Leads>
    </result>
</response>''')

        result = self.client.search_records(Lead, '')
        self.assertEqual(2, len(result))
        lead = result[0]
        self.assertTrue(isinstance(lead, Lead))
        self.assertEqual(lead['Company'], 'gsc.alti.mobi')
        self.assertEqual(lead['Lead Owner'], 'Khedija Ben Attaya')

    @requests_mock.mock()
    def test_get_record_by_id(self, m):
        m.get('https://crm.zoho.com/crm/private/xml/Leads/getRecordById',
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/getRecordById">
    <result>
        <Leads>
            <row no="1">
                <FL val="LEADID">1144270000007240021</FL>
                <FL val="SMOWNERID">1144270000003073200</FL>
                <FL val="Lead Owner">
                    <![CDATA[foo bar]]>
                </FL>
                <FL val="Company">
                    <![CDATA[foo.bar]]>
                </FL>
                <FL val="First Name">
                    <![CDATA[Ashish]]>
                </FL>
             </row>
        </Leads>
    </result>
</response>''')
        lead = self.client.get_record_by_id(Lead, '')
        self.assertTrue(isinstance(lead, Lead))
        self.assertEqual(lead['First Name'], 'Ashish')

    @requests_mock.mock()
    def test_update_records(self, m):
        """
        :type m: requests_mock.mocker.MockerCore
        """
        m.post('https://crm.zoho.com/crm/private/xml/Leads/updateRecords',
               text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/updateRecords">
    <result>
        <message>Record(s) updated successfully</message>
        <recorddetail>
            <FL val="Id">1144270000007254042</FL>
            <FL val="Created Time">2015-10-21 09:06:53</FL>
            <FL val="Modified Time">2015-10-21 11:48:58</FL>
            <FL val="Created By">
                <![CDATA[Cohen]]>
            </FL>
            <FL val="Modified By">
                <![CDATA[Cohen]]>
            </FL>
        </recorddetail>
    </result>
</response>''')
        lead = Lead(**{"Id": "1144270000007254042"})
        post_result = self.client.update_record(lead)
        self.assertTrue(isinstance(post_result, PostResult))
        self.assertEqual(post_result.detail['Id'], '1144270000007254042')
        self.assertEqual(post_result.detail['Created Time'], '2015-10-21 09:06:53')

    @requests_mock.mock()
    def test_get_fields(self, m):
        """
        :type m: requests_mock.mocker.MockerCore
        """
        m.get("https://crm.zoho.com/crm/private/xml/Leads/getFields",
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<Leads>
    <section name="Lead Information" dv="Lead Information">
        <FL req="false" type="Lookup" isreadonly="false" maxlength="120"  label="Lead Owner" dv="Lead Owner" customfield="false"></FL>
        <FL req="true" type="Text" isreadonly="false" maxlength="100"  label="Company" dv="Company" customfield="false"></FL>
        <FL req="false" type="Text" isreadonly="false" maxlength="100"  label="Designation" dv="Title" customfield="false"></FL>
        <FL req="true" type="Text" isreadonly="false" maxlength="80"  label="Last Name" dv="Last Name" customfield="false"></FL>
    </section>
</Leads>''')

        fields = self.client.get_fields("Leads")
        self.assertEqual(fields.sections[0].fields[0]['type'], 'Lookup')
        self.assertEqual(fields.sections[0]['dv'], 'Lead Information')

    @requests_mock.mock()
    def test_convert_lead(self, m):
        m.post("https://crm.zoho.com/crm/private/xml/Leads/convertLead",
               text='''<?xml version="1.0" encoding="UTF-8" ?>
<success>
    <Contact param="id">1144270000007264003</Contact>
    <Potential param="id">1144270000007264005</Potential>
    <Account param="id">1144270000007264001</Account>
</success>''')
        result = self.client.convert_lead('', ConvertLeadOption(), Potential())
        self.assertEqual(result.contact_id, '1144270000007264003')
        self.assertEqual(result.account_id, '1144270000007264001')
        self.assertEqual(result.potential_id, '1144270000007264005')

    @requests_mock.mock()
    def test_insert_record(self, m):
        m.post("https://crm.zoho.com/crm/private/xml/Leads/insertRecords",
               text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Leads/insertRecords">
    <result>
        <message>Record(s) added successfully</message>
        <recorddetail>
            <FL val="Id">1232949000000222001</FL>
            <FL val="Created Time">2015-10-23 18:43:48</FL>
            <FL val="Modified Time">2015-10-23 18:43:48</FL>
            <FL val="Created By">
                <![CDATA[Zhimin Wu]]>
            </FL>
            <FL val="Modified By">
                <![CDATA[Zhimin Wu]]>
            </FL>
        </recorddetail>
    </result>
</response>
''')
        result = self.client.insert_record(Lead(), duplicate_check='1')
        self.assertEquals(result.detail['Id'], '1232949000000222001')
        self.assertEquals(result.detail['Created By'], 'Zhimin Wu')

    @requests_mock.mock()
    def test_get_records_by_idlist(self, m):
        m.get('https://crm.zoho.com/crm/private/xml/Accounts/getRecordById',
              text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Accounts/getRecordById">
    <result>
        <Accounts>
            <row no="1">
                <FL val="ACCOUNTID">1144270000013672113</FL>
                <FL val="SMOWNERID">1144270000003073200</FL>
                <FL val="Payment Gateway">
                    <![CDATA[Paypal GSC]]>
                </FL>
            </row>
            <row no="2">
                <FL val="ACCOUNTID">1144270000013646060</FL>
                <FL val="SMOWNERID">1144270000011288005</FL>
                <FL val="Payment Gateway">
                    <![CDATA[null]]>
                </FL>
            </row>
        </Accounts>
    </result>
</response>
        ''')

        result = self.client.get_records_by_idlist(Account,
                                                   ['1144270000013672113', 'not_exist_id', '1144270000013646060'])
        self.assertEqual('1144270000013672113', result['1144270000013672113'].get_id())
        self.assertEqual('1144270000013646060', result['1144270000013646060'].get_id())
        self.assertEqual(None, result.get('not_exist_id'))

    @requests_mock.mock()
    def test_update_records(self, m):
        m.post('https://crm.zoho.com/crm/private/xml/Accounts/updateRecords',
               text='''<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/crm/private/xml/Accounts/updateRecords">
    <result>
        <row no="2">
            <success>
                <code>2001</code>
                <details>
                    <FL val="Id">2289386000000112001</FL>
                    <FL val="Created Time">2017-01-04 20:19:33</FL>
                    <FL val="Modified Time">2017-01-04 20:40:29</FL>
                    <FL val="Created By">
                        <![CDATA[Zhimin Wu]]>
                    </FL>
                    <FL val="Modified By">
                        <![CDATA[Zhimin Wu]]>
                    </FL>
                </details>
            </success>
        </row>
        <row no="1">
            <error>
                <code>401.2</code>
                <details>You do not have the permission to edit this record or the "id" value you have given is invalid.</details>
            </error>
        </row>
    </result>
</response>''')

        accounts = [
            Account(ACCOUNTID="228938600000011210"),
            Account(ACCOUNTID="2289386000000112001"),
        ]

        result = self.client.update_records(accounts)
        self.assertEqual(False, result['2289386000000112001'].error)
        self.assertEqual("2289386000000112001", result['2289386000000112001'].detail['Id'])
        self.assertEqual(True, result['228938600000011210'].error)


class DataTestCase(TestCase):
    def test_build_element(self):
        lead = Lead([('First Name', 'foo'), ('Last Name', 'bar')])
        element = Lead.wrap([lead, lead])
        self.assertEqual(element.find('./row/FL[@val="First Name"]').text, 'foo')
        self.assertEqual(element.findall('.//*/FL[@val="Last Name"]')[1].text, 'bar')

    def test_convert_lead_request(self):
        option = ConvertLeadOption(**{'createPotential': 'true'})
        potential = Potential(**{'Name': 'potential'})
        element = Potential.wrap([option, potential])
        self.assertEquals(element.tag, 'Potentials')
        self.assertEquals(element.find('.//*/option[@val="createPotential"]').text, 'true')
        self.assertEquals(element.find('.//*/FL[@val="Name"]').text, 'potential')


# noinspection PyBroadException
class RetryTest(TestCase):
    method_called = 0

    @classmethod
    def setUpClass(cls):
        import sys
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)

    @method_decorator(retry(max_retries=1))
    def retry_method(self):
        self.method_called += 1
        raise socket.timeout('timeout')

    def test_retry(self):
        self.called = 0

        @retry
        def timeout():
            self.called += 1
            raise socket.timeout('timeout')

        # noinspection PyBroadException
        try:
            timeout()
        except:
            pass

        self.assertEquals(self.called, 2)

        self.called = 0

        @retry(max_retries=0)
        def timeout():
            self.called += 1
            raise socket.timeout('timeout')

        try:
            timeout()
        except:
            pass

        self.assertEquals(self.called, 1)

        try:
            self.retry_method()
        except:
            pass

        self.assertEquals(self.method_called, 2)
