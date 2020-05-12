# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_product_category(apps, schema_editor):
    '''
    Populates product_category.default_product by random product of given
    product category.
    '''
    ProductCategory = apps.get_model('core', 'ProductCategory')
    Product = apps.get_model('core', 'Product')
    product = Product.objects \
        .filter(code='GSC_ENTERPRISE_ANNUAL_MONTHLY') \
        .first()
    ProductCategory.objects \
        .filter(default_product__isnull=True) \
        .update(default_product=product)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0061_auto_20180817_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='default_product',
            field=models.ForeignKey(related_name='default_for_categories', to='core.Product', null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='expiry_date',
            field=models.DateTimeField(null=True, blank=True),  # +blank=True
        ),
        migrations.RunPython(populate_product_category)
    ]
