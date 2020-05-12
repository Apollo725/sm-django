# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0053_auto_20180611_1422'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='old_plan',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='old_vendor_plan',
        ),
    ]
