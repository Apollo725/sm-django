# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_featureproductcategory_detail'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='billing_cycle',
            field=models.CharField(default='', max_length=12, choices=[(b'DATE_TO_DATE', 'Date to date'), (b'END_OF_MONTH', 'End of month')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='type',
            field=models.CharField(blank=True, max_length=50, choices=[(b'ADD', 'Add'), (b'NEW', 'New'), (b'UPDATE', 'Update')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(default=b'ACTIVE', max_length=31, choices=[(b'ACTIVE', 'Active'), (b'DETECTED', 'Detected'), (b'DRAFT', 'Draft'), (b'INACTIVE', 'Inactive')]),
        ),
    ]
