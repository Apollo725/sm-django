# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160314_0721'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcatalog',
            name='per_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productcatalog',
            name='self_service',
            field=models.BooleanField(default=False),
        ),
    ]
