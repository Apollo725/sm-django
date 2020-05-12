# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_customer_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='reseller_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
