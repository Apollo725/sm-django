# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_auto_20180607_0705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featureproductcategory',
            name='feature',
            field=models.ForeignKey(related_name='product_category_options', to='core.ProductFeature'),
        ),
        migrations.AlterField(
            model_name='featureproductcategory',
            name='product_category',
            field=models.ForeignKey(related_name='feature_options', to='core.ProductCategory'),
        ),
        migrations.AlterField(
            model_name='featureversion',
            name='feature',
            field=models.ForeignKey(related_name='version_options', to='core.ProductFeature'),
        ),
        migrations.AlterField(
            model_name='featureversion',
            name='version',
            field=models.ForeignKey(related_name='feature_options', to='core.ProductVersion'),
        ),
    ]
