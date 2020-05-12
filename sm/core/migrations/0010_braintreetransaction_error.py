# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_braintreepaymentmethod_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='braintreetransaction',
            name='error',
            field=models.TextField(null=True, blank=True),
        ),
    ]
