# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0060_productplan_billing_cycle'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='expiry',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='extension',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='from_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='minimal_order',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='refunded_amount',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='tax',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='to_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='type',
            field=models.CharField(blank=True, max_length=31, choices=[(b'ADD', 'Add'), (b'NEW', 'New'), (b'REFUND', 'Refund'), (b'RENEW', 'Renew'), (b'TRANSFER', b'Transfer'), (b'UPGRADE', 'Upgrade')]),
        ),
        migrations.AlterField(
            model_name='productplan',
            name='codename',
            field=models.CharField(unique=True, max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid'), (b'UNKNOWN_PLAN', b'Unknown plan')]),
        ),
    ]
