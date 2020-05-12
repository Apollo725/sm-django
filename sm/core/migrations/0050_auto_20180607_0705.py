# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_auto_20180604_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='logo_big',
            field=models.ImageField(null=True, upload_to=b'product_category/logo/big/', blank=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='logo_small',
            field=models.ImageField(null=True, upload_to=b'product_category/logo/small/', blank=True),
        ),
    ]
