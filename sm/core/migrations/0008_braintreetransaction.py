# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_sm_32'),
    ]

    operations = [
        migrations.CreateModel(
            name='BraintreeTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default=b'Not Completed', max_length=255)),
                ('completed_date', models.DateTimeField()),
                ('bt_id', models.CharField(default=b'', max_length=255)),
                ('order', models.OneToOneField(related_name='bt_transaction', to='core.Order')),
            ],
            options={
                'db_table': 'sm_bt_transaction',
            },
        ),
    ]
