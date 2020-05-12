# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_customer_last_payment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='plan',
            field=models.CharField(default='', max_length=31, blank=True, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='version',
            field=models.CharField(blank=True, max_length=31, choices=[(b'BASIC', 'Basic version'), (b'BUSINESS', 'Business version'), (b'ENTERPRISE', 'Enterprise version'), (b'FREE', 'Free version'), (b'PRO', 'Professional version')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_plan',
            field=models.CharField(default=b'ANNUAL_YEARLY', max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
    ]
