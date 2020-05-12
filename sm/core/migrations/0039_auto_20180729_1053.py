# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_auto_20180710_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='licenses',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='plan',
            field=models.CharField(blank=True, max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid'), (b'UNKNOWN_PLAN', b'Unknown plan')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='payment_method',
            field=models.CharField(default=b'PAYPAL_AUTO', max_length=63, blank=True, choices=[(b'OFFLINE', 'Offline'), (b'PAYPAL_AUTO', 'Paypal auto'), (b'PAYPAL_MANUAL', 'Paypal manual'), (b'PAYPAL_PREAPPROVED', 'Paypal preapproved')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, blank=True, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid'), (b'UNKNOWN_PLAN', b'Unknown plan')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='renewal_option',
            field=models.CharField(default=b'CANCEL', max_length=31, blank=True, choices=[(b'CANCEL', 'Cancel'), (b'FLEX', 'Flex'), (b'REDUCE', 'Reduce'), (b'RENEW', 'Renew')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='saw_price',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, blank=True, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid'), (b'UNKNOWN_PLAN', b'Unknown plan')]),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='customer',
            field=models.ForeignKey(related_name='vendor_profile_set', to='core.Customer'),
        ),
        migrations.AlterField(
            model_name='vendorvalue',
            name='sm_value',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
