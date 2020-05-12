# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_braintreecustomer_braintreesubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZohoContactRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contact_id', models.CharField(max_length=255, null=True, blank=True)),
                ('user', models.OneToOneField(to='core.User')),
            ],
            options={
                'db_table': 'sm_zoho_contact_record',
            },
        ),
        migrations.CreateModel(
            name='ZohoCustomerRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lead_id', models.CharField(max_length=255, null=True, blank=True)),
                ('account_id', models.CharField(max_length=255, null=True, blank=True)),
                ('potential_id', models.CharField(max_length=255, null=True, blank=True)),
                ('customer', models.OneToOneField(to='core.Customer')),
            ],
            options={
                'db_table': 'sm_zoho_customer_record',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionProxy',
            fields=[
            ],
            options={
                'verbose_name': 'Subscription View',
                'proxy': True,
                'verbose_name_plural': 'Subscriptions View',
            },
            bases=('core.subscription',),
        ),
        migrations.AlterField(
            model_name='braintreesubscription',
            name='bt_id',
            field=models.CharField(max_length=255, verbose_name=b'Braintree Id'),
        ),
    ]
