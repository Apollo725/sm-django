# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_auto_20180610_1337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
