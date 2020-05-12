# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_change_subscription_owner_to_payment_gateway'),
    ]

    operations = [
        migrations.CreateModel(
            name='BraintreePaymentMethod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('customer_id', models.CharField(max_length=255)),
                ('token', models.CharField(max_length=255)),
                ('succeed', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'sm_bt_payment_method',
            },
        ),
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('amount', models.FloatField(default=0)),
                ('start_at', models.DateTimeField(auto_now_add=True)),
                ('end_at', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'sm_discount_code',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='description',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='user',
            name='mock',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default=b'OPEN', max_length=31, choices=[(b'APPROVED', 'Approved'), (b'CANCELLED', 'Cancelled'), (b'DELIVERED', 'Delivered'), (b'INVOICE_SENT', 'Invoice sent'), (b'OPEN', 'Open'), (b'PAID', 'Paid'), (b'RENEWING', b'Renewing')]),
        ),
    ]
