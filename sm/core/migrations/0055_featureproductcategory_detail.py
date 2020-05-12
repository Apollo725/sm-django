# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0054_auto_20180611_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='featureproductcategory',
            name='detail',
            field=models.CharField(max_length=100, blank=True),
        ),
    ]
