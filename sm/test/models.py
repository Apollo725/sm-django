from django.db import models

from sm.core.models import Auditable



class MockZohoAccount(Auditable):
    id = models.AutoField(primary_key=True, verbose_name="Id")
    domain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domain")
    gsc_installed = models.CharField(max_length=31, blank=True, null=True, verbose_name="GSC Installed?")
    phone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Phone")
    gsc_install_status = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Install Status")
    lead_source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lead Source")
    total_revenue = models.CharField(max_length=255, blank=True, null=True, verbose_name="Total Revenue")
    payment_position = models.CharField(max_length=255, blank=True, null=True, verbose_name='Payment Position')
    first_payment_date = models.CharField(max_length=255, blank=True, null=True, verbose_name='First Payment Date')
    first_payment_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='First Payment ID')
    last_payment_date = models.CharField(max_length=255, blank=True, null=True, verbose_name='Last Payment Date')
    last_payment_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Last Payment ID')
    last_payment_outcome = models.CharField(max_length=255, blank=True, null=True, verbose_name='Last Payment Outcome')
    last_payment_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='Last Payment Type')
    account_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account Type')
    gsc_reseller_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Reseller_ID')
    account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account Name')
    gapps_version = models.CharField(max_length=255, blank=True, null=True, verbose_name='GAPPS Version')
    language_code = models.CharField(max_length=255, blank=True, null=True, verbose_name='Language Code')
    google_org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Google Organization Name')
    max_licenses = models.CharField(max_length=255, blank=True, null=True, verbose_name='Max licenses')
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name")
    admin_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Admin Email")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="First Name")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Last Name")
    communication_first_name = models.CharField(max_length=255, blank=True, null=True,
                                                verbose_name="Communication First Name")
    communication_last_name = models.CharField(max_length=255, blank=True, null=True,
                                               verbose_name="Communication Last Name")
    contact_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Contact ID')
    gsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC')
    account_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account ID')
    secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secondary Name")
    number_of_accounts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Accounts')
    number_of_licences = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Licences')
    gsc_install = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Install')
    gsc_expiry = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Expiry')
    gsc_status = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Status")
    gsc_commitment = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Commitment")
    gsc_renewal_option = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Renewal Option")
    gsc_version = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Version")
    cancelled_by_user = models.CharField(max_length=255, blank=True, null=True, verbose_name="Cancelled by User")
    billing_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Billing Code")
    billing_street = models.CharField(max_length=255, blank=True, null=True, verbose_name="Billing Street")
    billing_city = models.CharField(max_length=255, blank=True, null=True, verbose_name="Billing City")
    billing_state = models.CharField(max_length=255, blank=True, null=True, verbose_name="Billing State")
    braintree_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Braintree ID")
    paypal_failure = models.CharField(max_length=255, blank=True, null=True, verbose_name="Paypal Failure")
    paypal_gateway = models.CharField(max_length=255, blank=True, null=True, verbose_name="Paypal Gateway")
    trusted = models.CharField(max_length=255, blank=True, null=True, verbose_name="Trusted")
    main_contact_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Main Contact Email")
    reseller_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Reseller Email")
    google_reseller_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Google Reseller Name")
    gsc_stage = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC stage')

    class Meta:
        db_table = 'zoho_test_account'


class MockZohoLead(Auditable):
    id = models.AutoField(primary_key=True, verbose_name="Id")
    domain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domain")
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email")
    admin_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Admin Email")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="First Name")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Last Name")
    communication_first_name = models.CharField(max_length=255, blank=True, null=True,
                                                verbose_name="Communication First Name")
    communication_last_name = models.CharField(max_length=255, blank=True, null=True,
                                               verbose_name="Communication Last Name")
    contact_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Contact ID')
    gsc = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC')
    account_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account ID')
    account_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account Type')
    secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secondary Email")
    phone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Phone")
    gsc_install_status = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Install Status")
    lead_source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lead Source")
    gsc_reseller_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Reseller_ID')
    google_org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Google Organization Name')
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Company Name')
    language_code = models.CharField(max_length=31, blank=True, null=True, verbose_name='Language Code')
    apps_secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Apps Secondary Email')
    country_code = models.CharField(max_length=255, blank=True, null=True, verbose_name='Country Code')
    apps_creation = models.CharField(max_length=255, blank=True, null=True, verbose_name='Apps Creation')
    apps_expiry = models.CharField(max_length=255, blank=True, null=True, verbose_name='Apps Expiry')
    max_licenses = models.CharField(max_length=255, blank=True, null=True, verbose_name='Max licenses')
    number_of_accounts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Accounts')
    gapps_version = models.CharField(max_length=31, blank=True, null=True, verbose_name="GAPPS Version")
    offline_account = models.CharField(max_length=31, blank=True, null=True, verbose_name="Offline Account")
    subscription_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Subscription ID')
    subscription_name = models.CharField(max_length=511, verbose_name="Subscription Name")
    currency = models.CharField(max_length=31, blank=True, null=True, verbose_name="Currency")
    gsc_install = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Install')
    gsc_expiry = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Expiry')
    gsc_installed = models.CharField(max_length=31, blank=True, null=True, verbose_name="GSC Installed?")
    number_of_licences = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Licences')
    vendor_status = models.CharField(max_length=255, blank=True, null=True, verbose_name='Vendor Status')
    gsc_status = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Status')
    gsc_version = models.CharField(max_length=255, blank=True, null=True, verbose_name='GSC Version')

    class Meta:
        db_table = 'zoho_test_lead'


class MockZohoPotential(Auditable):
    id = models.AutoField(primary_key=True, verbose_name="Id")
    type = models.CharField(max_length=255, blank=True, null=True, verbose_name="Type")
    stage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Stage")
    amount = models.CharField(max_length=255, blank=True, null=True, verbose_name="Amount")
    payment_position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Payment Position")
    first_payment = models.CharField(max_length=255, blank=True, null=True, verbose_name="First Payment")
    closing_date = models.CharField(max_length=255, blank=True, null=True, verbose_name="Closing Date")
    gsc_version = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Version")
    gsc_status = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Status")
    gsc_commitment = models.CharField(max_length=255, blank=True, null=True, verbose_name="GSC Commitment")
    number_of_licences = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Licences')
    account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Account Name')
    smownerid = models.CharField(max_length=255, blank=True, null=True, verbose_name='SMOWNERID')
    potential_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Potential Name')
    upsell = models.CharField(max_length=255, blank=True, null=True, verbose_name='Upsell')

    class Meta:
        db_table = 'zoho_test_potential'


class MockZohoContact(Auditable):
    id = models.AutoField(primary_key=True, verbose_name="Id")
    domain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domain")
    google_org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Google Organization Name')
    phone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Phone")
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="First Name")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Last Name")
    mailing_zip = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mailing Zip")
    apps_secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Apps Secondary Email")
    language_code = models.CharField(max_length=31, blank=True, null=True, verbose_name='Language Code')
    number_of_accounts = models.CharField(max_length=255, blank=True, null=True, verbose_name='Number of Accounts')
    secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Secondary Email')

    class Meta:
        db_table = 'zoho_test_contact'


class MockZohoSalesOrder(Auditable):
    id = models.AutoField(primary_key=True, verbose_name="Id")
    subject = models.CharField(max_length=255, blank=True, null=True, verbose_name="Subject")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='First Name')
    potential_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Potential Name")
    account_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Account Name")
    product = models.CharField(max_length=255, blank=True, null=True, verbose_name="Product")
    quantity = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quantity")
    unit_price = models.CharField(max_length=255, blank=True, null=True, verbose_name="Unit Price")
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email")
    total_price = models.CharField(max_length=31, blank=True, null=True, verbose_name='TOTAL Price')

    class Meta:
        db_table = 'zoho_test_sales_order'


class GSCTestDomain(Auditable):
    domain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domain")
    license_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='License Number')
    plan = models.CharField(max_length=255, blank=True, null=True, verbose_name='Plan')
    status = models.CharField(max_length=255, blank=True, null=True, verbose_name='Status')
    primary = models.BooleanField(default=False, verbose_name="Is Primary")
    org_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Organization Name')
    lang = models.CharField(max_length=31, blank=True, null=True, verbose_name='Language Code')
    country = models.CharField(max_length=255, blank=True, null=True, verbose_name='Country Code')
    secondary_email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Secondary Email')
    users = models.IntegerField(blank=True, null=True, default=0, verbose_name='Users Number')
    apps_creation = models.DateTimeField(blank=True, null=True, verbose_name='Apps Creation')
    apps_expiry = models.DateTimeField(blank=True, null=True, verbose_name='Apps Expiry')
    apps_version = models.CharField(max_length=31, blank=True, null=True)
    max_licenses = models.IntegerField(blank=True, null=True, default=0, verbose_name='Max licenses')
    reseller = models.CharField(max_length=1023, blank=True, null=True)
    granted = models.BooleanField(default=False)
    registered = models.BooleanField(default=False)

    class Meta:
        db_table = 'gsc_test_domain'


def put_mock_gsc_license(subscription):
    result, _ = GSCTestDomain.objects.update_or_create(dict(
        domain=subscription.domain,
        plan=subscription.product.version,
        status=subscription.vendor_status,
        license_number=subscription.vendor_licenses
    ), domain=subscription.domain)

    return result


def get_gsc_test_granted_status(domain):
    domain = GSCTestDomain.objects.filter(domain=domain).first()
    assert isinstance(domain, GSCTestDomain)

    return domain.granted


def set_gsc_test_granted_status(domain):
    domain, _ = GSCTestDomain.objects.update_or_create(defaults=dict(granted=True), domain=domain)
    assert isinstance(domain, GSCTestDomain)

    return domain.granted


def get_test_vendor_profile(customer):
    profile = GSCTestDomain.objects.filter(domain=customer).values()
    if len(profile) > 0:
        profile = profile[0]
        del profile['created_at']
        del profile['modified_at']
        profile['name'] = profile['domain']
        del profile['domain']
        del profile['license_number']
        del profile['plan']
        del profile['status']
        del profile['id']
        return profile
    else:
        return {}
