# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import string
import random

from django.db import models, migrations
import sm.core.models


def populate_sku(apps, shema_editor):
    ProductVersion = apps.get_model('core', 'ProductVersion')
    used_random_strings = []
    for product_version in ProductVersion.objects.all():
        while 1:
            random_string = ''.join([random.choice(string.uppercase) for _ in xrange(10)])
            if random_string not in used_random_strings:
                break
        product_version.sku = random_string
        product_version.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_product_plan_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='productversion',
            name='sku',
            field=models.CharField(unique=False, null=True, max_length=100),
        ),
        migrations.RunPython(populate_sku),
        migrations.AlterField(
            model_name='productversion',
            name='sku',
            field=models.CharField(unique=True, null=False, max_length=100),
        ),
    ]
