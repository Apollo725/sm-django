# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from sm.core.models import ProductVersionEnum


def product_version_data_migration(apps, schema_editor):
    ProductVersion = apps.get_model('core', 'ProductVersion')
    Product = apps.get_model('core', 'Product')

    for version in ProductVersionEnum:
        products = Product.objects.filter(old_version=version.value)
        try:
            product_version = ProductVersion.objects.get(codename=version.value)
        except ProductVersion.DoesNotExist:
            continue

        products.update(version=product_version)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_pricing_refactoring'),
    ]

    operations = [
        migrations.RunPython(product_version_data_migration),
        migrations.RemoveField(
            model_name='product',
            name='old_version',
        ),
    ]
