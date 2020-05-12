# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_subscription_add_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='billing_cycle_end',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='billing_cycle_start',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
