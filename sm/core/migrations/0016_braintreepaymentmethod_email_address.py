# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20161211_0959'),
    ]

    operations = [
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='email_address',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
