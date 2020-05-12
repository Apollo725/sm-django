from __future__ import absolute_import
from sm.test.models import GSCTestDomain
import json

def mock():
    for info in [
        # name, domain, user_number, renewal_option
        ['gappsexperts.com', 'Gapps Experts', None, None, 'stef@econsulting.fr', 'PE', True, '2010-02-27T00:00:00Z', 'standard',
         50, 50, 'en'],
        ['econsulting.fr', 'Econsulting', 'econsulting', None, 'newlife2008.sc@gmail.com', 'FR', True, '2009-04-07T00:00:00Z', 'premier',
         8, 1246, 'fr'],
        ['alti.mobi', 'alti.mobi', "", None, 'stef@econsulting.fr', 'FR', True, '2011-09-15T00:00:00Z', 'standard',
         10, 10, 'en'],
        ['gappsexperts.com', 'Gapps Experts', None, None, 'stef@econsulting.fr', 'PE', True, '2010-02-27T00:00:00Z', 'standard',
         50, 50, 'en'],
    ]:
        domain, org_name, reseller, apps_expiry, secondary_email, country, primary, apps_creation, apps_version, users, max_licenses, lang = info

        GSCTestDomain.objects.update_or_create(defaults=dict(
            domain = domain,
            org_name = org_name,
            reseller = reseller,
            apps_expiry = apps_expiry,
            secondary_email = secondary_email,
            country = country,
            primary = primary,
            apps_creation = apps_creation,
            apps_version = apps_version,
            users = users,
            max_licenses = max_licenses,
            lang = lang,
        ), domain = domain)