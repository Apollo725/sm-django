# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20161212_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='last_payment_date_raw',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='last_payment_outcome_raw',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
