# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_product_category_for_gsc_products(apps, schema_editor):
    Product = apps.get_model('core', 'Product')   # noqa
    ProductCategory = apps.get_model('core', 'ProductCategory')   # noqa

    gsc_product_category = ProductCategory.objects.filter(code='GSC').first()
    if gsc_product_category:
        gsc_products = Product.objects.filter(name__icontains='gsc')
        gsc_products.update(category=gsc_product_category)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_remove_catalog_product_type'),
    ]

    operations = [
        migrations.RunPython(set_product_category_for_gsc_products, migrations.RunPython.noop),
    ]
