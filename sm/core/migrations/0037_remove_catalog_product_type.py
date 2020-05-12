# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_remove_subscription_unbound'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='catalog',
            name='product_type',
        ),
    ]
