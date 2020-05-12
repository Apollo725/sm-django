# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_subscription_cancelled_by_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='paypal_failure',
            field=models.BooleanField(default=False),
        ),
    ]
