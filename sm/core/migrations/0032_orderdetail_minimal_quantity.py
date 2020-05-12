# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20180109_0641'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='minimal_quantity',
            field=models.BooleanField(default=True),
        ),
    ]
