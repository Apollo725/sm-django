from sm.core.admin import *
from sm.test.models import *
from django.conf import settings


class ZohoLeadAdmin(admin.ModelAdmin):
    list_display = ('domain', 'gsc_version', 'gsc_install_status', 'number_of_licences')
    search_fields = ('domain',)


class ZohoPotentialAdmin(admin.ModelAdmin):
    list_display = ('potential_name', 'payment_position', 'gsc_version', 'amount')
    search_fields = ('potential_name', 'payment_position')


class ZohoContactAdmin(admin.ModelAdmin):
    list_display = ('domain', 'first_name', 'last_name', 'phone')
    search_fields = ('domain', 'phone')


class ZohoAccountAdmin(admin.ModelAdmin):
    list_display = ('domain', 'gsc_install_status', 'email')
    search_fields = ('domain', 'email')


class ZohoSalesOrderAdmin(admin.ModelAdmin):
    list_display = ('subject', 'potential_name', 'account_name', 'product')
    search_fields = ('subject', 'product')


class GSCTestDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'org_name', 'license_number', 'country', 'granted', 'registered')
    search_fields = ('domain', 'org_name')


if settings.TEST_MODE:
    admin.site.register(MockZohoLead, ZohoLeadAdmin)
    admin.site.register(MockZohoPotential, ZohoPotentialAdmin)
    admin.site.register(MockZohoContact, ZohoContactAdmin)
    admin.site.register(MockZohoAccount, ZohoAccountAdmin)
    admin.site.register(MockZohoSalesOrder, ZohoSalesOrderAdmin)
    admin.site.register(GSCTestDomain, GSCTestDomainAdmin)
