# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_change_braintree_transaction_order_foreignkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='cancelled_by_user',
            field=models.BooleanField(default=False),
        ),
    ]
