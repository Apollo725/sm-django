# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20170210_1853'),
    ]

    operations = [
        migrations.CreateModel(
            name='FailedTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('potential_id', models.CharField(max_length=63, null=True, blank=True)),
                ('error', models.CharField(max_length=255, null=True, blank=True)),
                ('order', models.ForeignKey(related_name='failed_transactions', to='core.Order')),
            ],
            options={
                'db_table': 'sm_failed_transactions',
            },
        ),
        migrations.AddField(
            model_name='customer',
            name='last_payment_id_raw',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
