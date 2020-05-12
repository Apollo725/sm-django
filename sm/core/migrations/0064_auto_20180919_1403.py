# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_auto_20180831_1032'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='braintreecustomer',
            table='sm_gt_customer'
        ),
        migrations.RunSQL(
            'ALTER SEQUENCE sm_bt_customer_id_seq RENAME TO '
            'sm_gt_customer_id_seq;'
        ),  # We do that only to make sequences naming non confusing for humans.
    ]
