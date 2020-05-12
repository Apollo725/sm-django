from __future__ import absolute_import

import logging
import sys
import time
import traceback
from functools import wraps

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

import zoho_api
from sm.product.gsc import models
from . import failed_transaction_manager

logger = logging.getLogger(__name__)
client = zoho_api.Client(token=settings.ZOHO_API_TOKEN)


class UpdateError(Exception):
    pass


def async(func):
    def inner(*args, **kwargs):
        if settings.TESTING:
            logger.info("Skip to execute zoho func %s %s %s", func, args, kwargs)
            return
        else:
            delay = kwargs.pop('delay', 0.5)
            if kwargs.pop('async', True):
                def new_func():
                    # noinspection PyBroadException
                    try:
                        time.sleep(delay)
                        func(*args, **kwargs)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        raise

                return zoho_api.executor.submit(new_func)
            else:
                return func(*args, **kwargs)

    return wraps(func)(inner)


time_format = "%Y-%m-%d %H:%M:%S"


def get_lead_criteria(domain, email):
    return "((Domain:%s)OR(Company:%s)OR(Email:%s))" % (domain, domain, email)


@async
def create_lead(user, detect_account=False):
    """

    :type user: models.User
    :param detect_account:
    """
    logger.info("creating lead %s ...", user)
    domain = user.customer.name

    if detect_account:
        record = get_zoho_customer_record(user.customer)
        if record and record.account_id:
            logger.info("Account has already existed %s", user.customer)
            update_account(user, client.get_record_by_id(zoho_api.Account, record.account_id), async=False)
            return
        else:
            if settings.TEST_MODE:
                records = client.dict_from_list(get_zoho_mock_account(domain, domain))
            else:
                records = client.search_records(zoho_api.Account, get_account_criteria(domain))
            if len(records) > 0:
                logger.info("Account has already existed %s in zoho", user.customer)
                update_account(user, records[0], async=False)
                return

    lead = None
    record = get_zoho_customer_record(user.customer)
    if record and record.lead_id:
        try:
            lead = client.get_record_by_id(zoho_api.Lead, record.lead_id)
        except zoho_api.NotFoundError:
            logger.exception("failed to load mock lead data with %s", record.lead_id)
            pass

    def _update_lead(_lead, _user):
        try:
            client.update_record(update_lead_fields(_lead, _user))
            update_lead_id(customer=_user.customer, lead_id=_lead.get_id())
            logger.info("succeed to update lead %s, id: %s", _user, _lead.get_id())
            return lead
        except zoho_api.Error:
            logger.exception("failed to update lead %s", _user)
            raise

    if not lead:
        if settings.TEST_MODE:
            leads = get_zoho_mock_lead(user.customer.name, user.customer.name, user.email)
        else:
            leads = client.search_records(zoho_api.Lead, get_lead_criteria(user.customer.name, user.email))

        if len(leads) > 0:
            lead = leads[0]

    if lead:
        return _update_lead(_lead=lead, _user=user)

    lead = zoho_api.Lead()
    update_lead_fields(lead, user)

    try:
        lead = client.insert_record(lead, True)
        update_lead_id(user.customer, lead.detail.get_id())
        logger.info("succeed to insert lead %s, id: %s", domain, lead.detail.get_id())
    except zoho_api.Error as e:
        logger.exception("failed to insert lead %s", domain)
        raise e

    try:
        lead = client.get_record_by_id(zoho_api.Lead, lead.detail.get_id())
        return lead
    except zoho_api.Error as e:
        logger.exception("failed to find lead %s just inserted", domain)
        raise e


def update_lead_fields(lead, user):
    vendor_profile = models.try_to_get_vendor_profile(user.customer)
    subscription = models.SubscriptionManager(user.customer).get_subscription()
    # according to
    # https://docs.google.com/document/d/1lglyD10a4kPqVkL7jSOje7GKclxNK7ZGdUqPqXOqJLw/edit#bookmark=id.jgwq8tohmaor
    # https://docs.google.com/spreadsheets/d/1R7w83JkCSyPgqzcYrFQ3pkK6MKknLBARbHZStXumkJc/edit#gid=0

    lead['Email'] = user.email
    lead['Domain'] = user.customer.name
    lead['Admin Email'] = user.email

    lead['Last Name'] = user.name.split(" ")[-1]
    lead['First Name'] = user.name.split(" ")[0]

    lead['Communication First Name'] = lead['First Name']
    lead['Communication Last Name'] = lead['Last Name']

    lead['Contact ID'] = user.id

    lead['GSC'] = 'true'
    lead['Account ID'] = user.customer.id
    lead['Account Type'] = user.customer.get_type_display()

    lead['Secondary Email'] = user.contact_email
    lead['Phone'] = user.phone_number
    lead['GSC Install Status'] = user.customer.install_status
    lead['Lead Source'] = user.customer.source or "GSC Install"

    customer = user.customer

    if customer.reseller:
        record = get_zoho_customer_record(customer.reseller)
        if record:
            lead['GSC Reseller_ID'] = record.account_id

    if vendor_profile:
        lead['Google Organization Name'] = vendor_profile.org_name
        lead['Company'] = vendor_profile.org_name or user.customer.name
        lead['Language Code'] = vendor_profile.lang
        lead['Secondary Email'] = user.contact_email or vendor_profile.secondary_email
        lead['Apps Secondary Email'] = user.contact_email or vendor_profile.secondary_email
        lead['Country Code'] = vendor_profile.country

        lead['Apps Creation'] = format_date(vendor_profile.apps_creation)
        lead['Apps Expiry'] = format_date(vendor_profile.apps_expiry)

        lead['Max Licences'] = vendor_profile.max_licenses
        lead['Number Of Accounts'] = vendor_profile.users
        lead['GAPPS Version'] = vendor_profile.apps_version
        lead['Offline Account'] = 'NO'

    if subscription:
        lead['Subscription ID'] = subscription.id
        lead['Subscription name'] = subscription.name
        lead['Currency'] = vendor_profile.currency
        lead['GSC Install'] = format_date(subscription.install_date)
        lead['GSC Expiry'] = format_date(subscription.expiry_date)
        lead['GSC Installed?'] = 'true'
        lead['Number of Licences'] = subscription.vendor_licenses or vendor_profile.users
        lead['Vendor Status'] = subscription.vendor_status
        lead['GSC Status'] = subscription.vendor_status
        if subscription.product:
            lead['GSC Version'] = subscription.product.version

    return lead


def get_account_criteria(domain):
    # TODO(greg_eremeev) HIGH: if you change this condition then change
    #                          create_account_before_search_zoho_records decorator
    return "((Domain:%s)OR(Account Name:%s))" % (domain, domain)


def get_contact_criteria(domain, email):
    return "((Email:%s)OR(Account Name:%s)OR(Domain:%s))" % (email, domain, domain)


def update_account_fields(account, user, vendor_products=None):
    """
    :param vendor_products: dictionary {"prod_key": no_of_licenses}
        send dictionary of vendor products with number of licenses
        to be sent with account as well
    """
    account = zoho_api.Account(**account)   # copy data
    customer = user.customer
    profile = models.get_profile(customer)
    subscription = models.SubscriptionManager(user.customer).get_subscription()
    vendor_profile = models.try_to_get_vendor_profile(customer)
    assert isinstance(customer, models.Customer)

    account['Domain'] = user.customer.name
    account['GSC Installed?'] = 'true'
    account['Phone'] = user.phone_number

    account['GSC Install Status'] = user.customer.install_status
    account['Lead Source'] = user.customer.source or "GSC Install"

    # update gsc financial
    account['Total Revenue'] = customer.total_revenue
    account['Payment Position'] = customer.payment_position

    account['First Payment Date'] = format_date(customer.first_payment_date)
    account['First Payment ID'] = customer.first_payment_id

    account['Last Payment Date'] = format_date(customer.last_payment_date)

    account['Last Payment ID'] = customer.last_payment_id

    account['Last Payment Outcome'] = customer.last_payment_outcome or ''
    account['Last Payment Amount'] = customer.last_payment_amount or ''
    account['Last Payment Type'] = get_checkout_type(customer.last_payment_type or '')
    account['Account Type'] = customer.get_type_display()

    if customer.reseller:
        record = get_zoho_customer_record(customer.reseller)
        if record:
            account['GSC Reseller_ID'] = record.account_id

    if vendor_profile and subscription:
        account['Account Name'] = vendor_profile.org_name or user.customer.name
        account['GAPPS Version'] = vendor_profile.apps_version
        account['Google Organization Name'] = vendor_profile.org_name
        account['Language Code'] = vendor_profile.lang
        account['Max Licences'] = vendor_profile.max_licenses
        account['Number Of Accounts'] = vendor_profile.users
        account['Number of Licences'] = subscription.vendor_licenses or vendor_profile.users
        account['GSC Install'] = format_date(subscription.install_date)
        account['GSC Expiry'] = format_date(subscription.expiry_date)
        account['GSC Status'] = subscription.vendor_status
        account['GSC Commitment'] = subscription.plan.codename
        account['GSC Renewal Option'] = subscription.renewal_option
        if subscription.product:
            account['GSC Version'] = subscription.product.version.codename
        account["Cancelled by User"] = subscription.cancelled_by_user

    if profile:
        account['Billing Code'] = profile.zip_code
        account['Billing Street'] = profile.address
        account['Billing City'] = profile.city
        account['Billing State'] = profile.state
        account['Billing Country'] = profile.country

    account["Braintree ID"] = get_braintree_id(user)

    if subscription:
        account["Paypal Failure"] = subscription.paypal_failure
        account["Payment Gateway"] = subscription.payment_gateway
        account["Trusted"] = subscription.trusted

    communication_user = customer.get_communication_user()
    if communication_user:
        account['Communication First Name'] = communication_user.name.split(' ')[0]
        account['Communication Last Name'] = communication_user.name.split(' ')[-1]
        contact_email = communication_user.contact_email
        if not contact_email:
            contact_email = communication_user.email
        account['Main Contact Email'] = contact_email

    if customer.reseller:
        reseller = get_zoho_customer_record(customer.reseller)
        if reseller and reseller.account_id:
            account['GSC Reseller_ID'] = reseller.account_id
        account['GSC Reseller'] = customer.reseller.verbose_name
        reseller_user = customer.reseller.get_communication_user()
        if reseller_user:
            account['Reseller Email'] = reseller_user.contact_email or reseller_user.email
    else:
        account['Google Reseller Name'] = customer.reseller_name

    if vendor_products:
        for key in vendor_products.keys():
            account[key] = vendor_products[key]

    return account


def get_braintree_id(user):
    return 'sm_' + user.auth_user.username


def update_contact_fields(contact, user):
    contact = zoho_api.Contact(**contact)
    vendor_profile = models.try_to_get_vendor_profile(user.customer)
    profile = models.get_profile(user.customer)

    contact['Domain'] = user.customer.name
    contact['Google Organization Name'] = user.customer.org_name
    contact['Phone'] = user.phone_number
    contact['Email'] = user.email
    contact['Domain'] = user.customer.name
    contact['Admin Email'] = user.email
    contact['Last Name'] = user.name.split(" ")[-1]
    contact['First Name'] = user.name.split(" ")[0]

    if profile:
        contact['Mailing Zip'] = profile.zip_code

    if vendor_profile:
        contact['Apps Secondary Email'] = user.contact_email or vendor_profile.secondary_email
        contact['Language Code'] = vendor_profile.lang
        contact['Number Of Accounts'] = vendor_profile.users
        contact['Secondary Email'] = user.contact_email or vendor_profile.secondary_email

    return contact


@async
def update_account(user_or_customer, account=None, context=None, vendor_products=None):
    """
    """
    if isinstance(user_or_customer, models.Customer):
        user = user_or_customer.get_communication_user()
    else:
        user = user_or_customer

    try:
        if account:
            to_update = update_account_fields(account, user, vendor_products=vendor_products)
            account = client.update_record(to_update).detail
            logger.info("Succeed to update account %s", user)
            update_account_id(customer=user.customer, account_id=account.get_id())
            return account
        else:
            record = get_zoho_customer_record(user.customer)
            if record and record.account_id:
                account = client.get_record_by_id(zoho_api.Account, record.account_id)
                update_account(user, account, context=context, async=False, vendor_products=vendor_products)
            else:
                accounts = client.search_records(zoho_api.Account, get_account_criteria(user.customer.name))
                if len(accounts) == 0:
                    raise UpdateError("Can't find any account %s" % user.customer.name)
                update_account(user, accounts[0], context=context, async=False, vendor_products=vendor_products)
                update_account_id(customer=user.customer, account_id=accounts[0].get_id())
    except zoho_api.Error as e:
        logger.exception("Failed to update account %s", user.email)
        raise e


@async
def update_contact(user, contact=None):
    try:
        if contact:
            to_update = update_contact_fields(contact, user)
            contact = client.update_record(to_update).detail
            logger.info("Succeed to update contact %s", user)
            return contact
        else:
            record = get_zoho_user_record(user)
            if record and record.contact_id:
                contact = client.get_record_by_id(zoho_api.Contact, record.contact_id)
                update_contact(user, contact)
            else:
                contacts = client.search_records(zoho_api.Contact, get_contact_criteria(user.customer.name, user.email))
                if len(contacts) == 0:
                    contact = zoho_api.Contact()
                    contact = update_contact_fields(contact, user)
                    result = client.insert_record(contact, True)
                    update_contact_id(user, contact_id=result.detail.get_id())
                else:
                    update_contact(user, contacts[0])
                    update_contact_id(user, contact_id=contacts[0].get_id())
    except zoho_api.Error as e:
        logger.exception("Failed to update contact %s", user.email)
        raise e


def get_zoho_customer_record(customer):
    # type: (models.Customer) -> models.ZohoCustomerRecord
    return models.ZohoCustomerRecord.objects.filter(customer=customer).first()


def get_zoho_user_record(user):
    return models.ZohoContactRecord.objects.filter(user=user).first()


def get_zoho_mock_account(domain, name):
    return models.MockZohoAccount.objects.filter(domain=domain, account_name=name).values()


def get_zoho_mock_lead(domain, company_name, email):
    return models.MockZohoLead.objects.filter(domain=domain, company_name=company_name, email=email).values()


def update_lead_id(customer, lead_id):
    obj, _ = models.ZohoCustomerRecord.objects.update_or_create(defaults={
        'lead_id': lead_id
    }, customer=customer)
    return obj


def update_account_id(customer, account_id):
    obj, _ = models.ZohoCustomerRecord.objects.update_or_create(
        defaults={
            'account_id': account_id
        }, customer=customer
    )

    return obj


def format_date(date):
    if date:
        return date.strftime(time_format)
    return ""


def update_contact_id(user, contact_id):
    obj, _ = models.ZohoContactRecord.objects.update_or_create(
        defaults={
            'contact_id': contact_id
        },
        user=user
    )

    return obj


def update_potential_id(customer, potential_id):
    obj, _ = models.ZohoCustomerRecord.objects.update_or_create(
        defaults={
            'potential_id': potential_id
        }, customer=customer
    )

    return obj


def lead_converted_just_now(user):
    def get_key(user):
        return "convert_lead_%s" % user.pk

    ret = cache.get(get_key(user))
    cache.set(get_key(user), "true", timeout=10)
    return ret is not None


def create_account(user, vendor_profile):
    logger.info("find no account or contact %s, try to create lead", user)
    lead = create_lead(user, async=False)
    if not lead:
        logger.exception("failed to convert lead %s", user)
        return

    try:
        pro = models.get_default_catalog().get_tier(
            vendor_profile.users or 5,
            version=models.ProductVersionEnum.PRO,
            plan=models.SubscriptionPlan.ANNUAL_YEARLY)

        price = float(pro.price)

        if vendor_profile.apps_version and vendor_profile.apps_version.lower() != 'premier':
            price *= 0.7

        option = zoho_api.ConvertLeadOption({'notifyLeadOwner': 'false'})
        if lead.get('SMOWNERID', None):
            option['assignTo'] = lead['SMOWNERID']

        potential = zoho_api.Potential({
            'Potential Name': 'GSC for %s' % user.customer.name,
            'Closing Date': format_date(timezone.now() + relativedelta(days=15)),
            'Amount': price,
            'X-Step process': 'Step 1',
            'Potential Stage': 'Just Installed',
            'Type': 'New Business'
        })

        if settings.TEST_MODE:
            result = client.convert_lead_by_mock(lead.get_id(), potential)
        else:
            result = client.convert_lead(lead.get_id(), option, potential)

        record, _ = models.ZohoCustomerRecord.objects.update_or_create(customer=user.customer)
        record.account_id = result.account_id
        record.potential_id = result.potential_id
        record.save()

        record, _ = models.ZohoContactRecord.objects.update_or_create(user=user)
        record.contact_id = result.contact_id
        record.save()

        logger.info("succeed to convert lead %s %s, "
                    "account id: %s, contact id: %s, potential id: %s",
                    lead.get_id(), user.email,
                    result.account_id,
                    result.contact_id,
                    result.potential_id
                    )

    except zoho_api.Error as e:
        logger.exception("Failed to convert lead %s %s", lead.get_id(), user.email)
        raise e


@async
def convert_lead(user):
    """

    :type user: models.User
    """
    if lead_converted_just_now(user):
        logger.info("Lead is just converted %s", user)
        return

    logger.info('converting lead %s', user)
    domain = user.customer.name
    vendor_profile = models.get_vendor_profile(user.customer)
    account = None

    customer_record = get_zoho_customer_record(user.customer)

    if customer_record and customer_record.account_id:
        account = client.get_record_by_id(zoho_api.Account, customer_record.account_id)
    else:
        if settings.TEST_MODE:
            accounts = client.dict_from_list(get_zoho_mock_account(domain, domain))
        else:
            accounts = client.search_records(zoho_api.Account, get_account_criteria(domain))
        if len(accounts) > 0:
            account = accounts[0]
            update_account_id(user.customer, account.get_id())

    if not account:
        create_account(user, vendor_profile)

    else:
        update_account(user, account=account, async=False)
        update_contact(user, async=False)


@async
def price_viewed(user):
    record = get_zoho_customer_record(user.customer)
    if record and record.account_id:
        account = client.get_record_by_id(zoho_api.Account, record.account_id)

        if 'GSC stage' not in account or (settings.TEST_MODE and account['GSC stage'] is None):
            account['GSC stage'] = 'Price viewed'
            try:
                client.update_record(account)
                logger.info("Succeed to change gsc stage %s", user)
            except zoho_api.Error as e:
                logger.exception("Failed to update gsc stage %s", user)
                raise e


def get_potential_criteria(name):
    return "((Potential Name:GSC for %s)OR(Domain:%s))" % (name, name)


def get_potential_by_id(potential_id):
    try:
        return client.get_record_by_id(zoho_api.Potential, potential_id)
    except zoho_api.NotFoundError:
        logger.warn("Can't find potential with id %s", potential_id)
        return None


def get_potential(customer):
    record = get_zoho_customer_record(customer)
    if record and record.potential_id:
        return get_potential_by_id(record.potential_id)
    return None


@async
def update_potential(order_detail, checkout_type):
    customer = order_detail.order.customer
    potential = get_potential(customer)

    if not potential:
        create_potential(order_detail, checkout_type)
        return

    account = get_account(customer)
    potential = update_potential_fields(
        potential=potential,
        order_detail=order_detail,
        checkout_type=checkout_type,
        failed=False,
        account=account
    )

    try:
        client.update_record(potential)
        logger.info("succeeded to update potential %s", potential)
    except zoho_api.Error as e:
        logger.exception("Failed to update potential %s", potential)
        raise e


def get_first_payment_order(customer):
    order = models.Order.objects.filter(
        status=models.OrderStatus.PAID, customer=customer).order_by('date').first()
    if order:
        assert isinstance(order, models.Order)
        return order


def get_last_payment_order(customer):
    order = models.Order.objects.filter(
        status=models.OrderStatus.PAID, customer=customer).order_by('-date').first()
    if order:
        assert isinstance(order, models.Order)
        return order


def get_payment_id(order):
    bt_tx = models.BraintreeTransaction.objects.filter(order=order).first()
    if bt_tx:
        assert isinstance(bt_tx, models.BraintreeTransaction)
        return "braintree:" + bt_tx.bt_id
    else:
        paypal_tx = models.PaypalTransaction.objects.filter(order=order).first()
        if paypal_tx:
            assert isinstance(paypal_tx, models.PaypalTransaction)
            return "paypal:" + paypal_tx.txn_id
    return ""


def get_account(customer):
    record = get_zoho_customer_record(customer)

    if record and record.account_id:
        try:
            return client.get_record_by_id(zoho_api.Account, record.account_id)
        except zoho_api.NotFoundError:
            logger.exception("Account (%s) is not found", customer)
            return None
    else:
        accounts = client.search_records(zoho_api.Account, get_account_criteria(customer.name))
        if len(accounts) > 0:
            account = accounts[0]
            update_account_id(customer, account.get_id())
            return account
        else:
            logger.exception("Account (%s) is not found", customer)

    return


@async
def update_failed_potential(order_detail, failed_transaction, checkout_type):
    customer = order_detail.order.customer
    account = get_account(customer)
    new = False

    potential = None
    if failed_transaction.potential_id:
        try:
            potential = client.get_record_by_id(zoho_api.Potential, failed_transaction.potential_id)
        except zoho_api.NotFoundError:
            pass

    if not potential:
        potential = zoho_api.Potential()
        new = True

    potential = update_potential_fields(
        potential=potential,
        order_detail=order_detail,
        checkout_type=checkout_type,
        failed=True,
        account=account
    )

    try:
        if not new:
            client.update_record(
                potential
            )
            logger.info("succeed to update potential %s", potential.get('Potential Name'))
        else:
            result = client.insert_record(potential, wf_trigger=True)
            failed_transaction_manager.update_potential_id(
                failed_transaction, result.detail.get_id()
            )
            logger.info("succeed to insert potential %s", potential.get('Potential Name'))
    except zoho_api.Error:
        logger.exception("Failed to update %s", potential)
        raise


@async
def create_potential(order_detail, checkout_type, potential_id=None):
    """

    :param checkout_type: checkout type in [renewal, add, upgradePack, upgrade]
    :type order_detail: models.OrderDetail
    :param potential_id: str
    """
    customer = order_detail.order.customer
    account = get_account(customer)
    potential = None
    new = False

    if potential_id:
        potential = get_potential_by_id(potential_id)

    if not potential:
        potential = zoho_api.Potential()
        new = True

    potential = update_potential_fields(
        potential=potential,
        order_detail=order_detail,
        checkout_type=checkout_type,
        failed=False,
        account=account
    )

    try:
        if not new:
            client.update_record(
                potential
            )
            logger.info("succeed to update potential %s", potential.get('Potential Name'))
        else:
            client.insert_record(potential, wf_trigger=True)
            logger.info("succeed to create potential %s", potential.get('Potential Name'))
    except zoho_api.Error:
        logger.exception("Failed to update %s", potential)
        raise


def update_potential_fields(
        potential,
        order_detail,
        checkout_type,
        failed=False,
        account=None
):
    order = order_detail.order
    customer = order.customer
    subscription = order_detail.subscription

    payment_position = models.Order.objects.filter(
        status=models.OrderStatus.PAID,
        customer=customer
    ).count()

    if failed:
        payment_position += 1

    potential_type = get_checkout_type(checkout_type)
    potential['Type'] = potential_type

    if not failed:
        potential['Stage'] = 'Paid - Closed Won'
    else:
        potential['Stage'] = 'Close - Lost'

    potential['Amount'] = order_detail.total
    potential['Payment Position'] = payment_position
    potential['First Payment'] = format_date(customer.first_payment_date)
    potential['Closing Date'] = format_date(timezone.now())
    potential['GSC Version'] = order_detail.product.version
    potential['GSC Status'] = subscription.vendor_status
    potential['GSC Expiry'] = format(subscription.expiry_date)
    potential['GSC Commitment'] = order_detail.product.plan
    potential['Number of Licences'] = order_detail.amount

    if account:
        potential['Account Name'] = account['Account Name'] if 'Account Name' in account else ''
        potential['SMOWNERID'] = account['SMOWNERID'] if 'SMOWNERID' in account else ''
    else:
        potential['Account Name'] = customer.verbose_name

    potential['Potential Name'] = '%s GSC %s %s for %s (%s)' % (
        potential_type,
        order_detail.product.version,
        order_detail.product.plan,
        customer.name,
        payment_position
    )

    if not failed:
        if ((order_detail.product.monthly and payment_position <= 12) or
                (not order_detail.product.monthly and payment_position == 1)):
            potential["Upsell"] = "True"

    return potential


TYPE_MAPPING = {
    'first': 'RESUBSCRIPTION',
    'add': 'ADDITION',
    'upgrade': 'UPGRADE',
    'upgradePack': 'UPGRADE_PACK',
    'renewal': 'RENEWAL',
    'new': 'NEW'
}


def get_checkout_type(checkout_type):
    return TYPE_MAPPING.get(checkout_type.lower(), checkout_type.upper())


def create_tmp_lead(datas):
    domain = datas.data['domain']

    lead_datas = zoho_api.Lead()
    lead_datas['First Name'] = datas.data['first_name']
    lead_datas['Last Name'] = datas.data['last_name']
    lead_datas['Email'] = datas.data['email']
    lead_datas['Company'] = datas.data['company']
    lead_datas['Domain'] = domain
    lead_datas['Phone'] = datas.data['phone']

    lead_datas['Street'] = datas.data['street_address']
    lead_datas['City'] = datas.data['city']
    lead_datas['State'] = datas.data['state']
    lead_datas['Zip Code'] = datas.data['zip']
    lead_datas['Country'] = datas.data['country']
    lead_datas['Description'] = datas.data['message']

    lead_datas['Lead Source'] = datas.data['lead_source']
    lead_datas['Webform'] = datas.data['web_form']

    try:
        lead = client.insert_record(lead_datas, True)
        lead_id = lead.detail.get_id()
        # update_lead_id(user.customer, lead.detail.get_id())
        logger.info("succeed to insert temporary lead %s, id: %s", domain, lead_id)
    except zoho_api.Error:
        logger.exception("failed to insert temporary lead %s", domain)
        raise

    try:
        return client.get_record_by_id(zoho_api.Lead, lead_id).get_id()
    except zoho_api.Error:
        logger.exception("failed to find lead %s just inserted", domain)
        raise
