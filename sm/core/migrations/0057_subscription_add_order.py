# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_auto_20180622_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='add_order',
            field=models.CharField(default='PRORATE', max_length=7, choices=[(b'EXTEND', 'Extend'), (b'PRORATE', 'Prorate')]),
            preserve_default=False,
        ),
    ]
