# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_auto_20180422_0940'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productcategory',
            options={'verbose_name_plural': 'product categories'},
        ),
        migrations.AlterField(
            model_name='productcategory',
            name='parent_category',
            field=models.ForeignKey(related_name='child_category', blank=True, to='core.ProductCategory', null=True),
        ),
        migrations.AlterField(
            model_name='productcategory',
            name='vendor',
            field=models.ForeignKey(blank=True, to='core.Vendor', null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(default=b'ACTIVE', max_length=31, choices=[(b'ACTIVE', 'Active'), (b'DETECTED', 'Detected'), (b'DRAFT', 'Draft'), (b'INACTIVE', 'Inactive')]),
        ),
    ]
