# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_auto_20180704_1132'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='unbound',
        ),
    ]
