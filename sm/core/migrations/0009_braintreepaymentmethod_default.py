# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_braintreetransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='default',
            field=models.BooleanField(default=False),
        ),
    ]
