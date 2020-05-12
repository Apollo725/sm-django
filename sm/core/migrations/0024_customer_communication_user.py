# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20170126_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='communication_user',
            field=models.ForeignKey(related_name='+', blank=True, to='core.User', null=True),
        ),
    ]
