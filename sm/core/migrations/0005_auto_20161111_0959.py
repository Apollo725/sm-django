# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20160328_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='install_status',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='registered',
            field=models.BooleanField(default=False),
        ),
    ]
