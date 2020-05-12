# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20170406_0329'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='last_payment_type',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
