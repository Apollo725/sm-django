# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_auto_20180422_0940'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleTransferToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(max_length=255)),
                ('customer', models.ForeignKey(to='core.Customer')),
            ],
            options={
                'db_table': 'gsuite_transfer_token',
            },
        ),
    ]
