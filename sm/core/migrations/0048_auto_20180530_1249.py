# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_auto_20180529_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='displayproduct',
            name='type',
            field=models.CharField(max_length=50, null=True, choices=[(b'NEW', 'New'), (b'UPDATE', 'Update')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(related_name='products', to='core.ProductCategory', null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='version',
            field=models.ForeignKey(related_name='products', to='core.ProductVersion', null=True),
        ),
    ]
