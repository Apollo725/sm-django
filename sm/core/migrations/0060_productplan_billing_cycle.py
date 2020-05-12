# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0059_auto_20180628_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='productplan',
            name='billing_cycle',
            field=models.CharField(default='', max_length=12, choices=[(b'DATE_TO_DATE', 'Date to date'), (b'END_OF_MONTH', 'End of month')]),
            preserve_default=False,
        ),
    ]
