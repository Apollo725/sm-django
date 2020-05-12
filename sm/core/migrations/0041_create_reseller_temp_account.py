# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_auto_20180801_0809'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResellerTempAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('t_stamp', models.DateTimeField(auto_now_add=True)),
                ('zoho_lead_id', models.CharField(max_length=255, db_index=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('domain', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=255)),
                ('street_address', models.CharField(default=b'', max_length=255, blank=True)),
                ('city', models.CharField(default=b'', max_length=255, blank=True)),
                ('state', models.CharField(default=b'', max_length=255, blank=True)),
                ('zip', models.CharField(default=b'', max_length=255, blank=True)),
                ('country', models.CharField(default=b'', max_length=255, blank=True)),
                ('message', models.CharField(default=b'', max_length=1024, blank=True)),
                ('lead_source', models.CharField(default=b'', max_length=1024, blank=True)),
                ('web_form', models.CharField(default=b'', max_length=1024, blank=True)),
                ('lang', models.CharField(default=b'', max_length=1024, blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_status',
            field=models.CharField(default=b'EVAL', max_length=31, blank=True, choices=[(b'ACTIVE', b'ACTIVE'), (b'BILLING_ACTIVATION_PENDING', b'BILLING_ACTIVATION_PENDING'), (b'CANCELLED', b'CANCELLED'), (b'EVAL', b'EVAL'), (b'EXPIRED', b'EXPIRED'), (b'EXPIRED_EVAL', b'EXPIRED_EVAL'), (b'EXPIRED_PAID', b'EXPIRED_PAID'), (b'PAID', b'PAID'), (b'PENDING', b'PENDING'), (b'SUSPENDED', b'SUSPENDED'), (b'UNINSTALLED_EVAL', b'UNINSTALLED_EVAL'), (b'UNINSTALLED_EXPIRED', b'UNINSTALLED_EXPIRED'), (b'UNINSTALLED_PAID', b'UNINSTALLED_PAID')]),
        ),
    ]
