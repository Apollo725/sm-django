# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20170214_0853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='plan',
            field=models.CharField(max_length=31, null=True, choices=[(b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, choices=[(b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, choices=[(b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
    ]
