# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BraintreeCustomer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bt_id', models.CharField(max_length=255)),
                ('user', models.ForeignKey(to='core.User')),
            ],
            options={
                'db_table': 'sm_bt_customer',
            },
        ),
        migrations.CreateModel(
            name='BraintreeSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('bt_id', models.CharField(max_length=255)),
                ('status', models.CharField(default=b'Active', max_length=255)),
                ('detail', models.TextField()),
                ('cancelled', models.BooleanField(default=False)),
                ('subscription', models.ForeignKey(related_name='bt', to='core.Subscription')),
            ],
            options={
                'db_table': 'sm_bt_subscription',
            },
        ),
    ]
