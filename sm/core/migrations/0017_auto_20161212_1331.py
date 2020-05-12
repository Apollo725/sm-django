# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_braintreepaymentmethod_email_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='braintreepaymentmethod',
            name='expiration_date',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
