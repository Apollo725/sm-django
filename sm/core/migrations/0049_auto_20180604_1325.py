# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_null_records_in_featureversion(apps, schema_editor):
    FeatureVersion = apps.get_model('core', 'FeatureVersion')
    for feature_version in FeatureVersion.objects.all():
        feature_version.detail = ''
        feature_version.save()


def remove_null_records_in_displayproduct(apps, schema_editor):
    DisplayProduct = apps.get_model('core', 'DisplayProduct')
    for display_product in DisplayProduct.objects.all():
        display_product.type = ''
        display_product.save()


def remove_null_records_in_product(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    for product in Product.objects.all():
        product.unit = ''
        product.unit_plural = ''
        product.save()


def remove_null_records_in_productplan(apps, schema_editor):
    ProductPlan = apps.get_model('core', 'ProductPlan')
    for product_plan in ProductPlan.objects.all():
        product_plan.alternate_frequency = ''
        product_plan.commitment = ''
        product_plan.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_auto_20180530_1249'),
    ]

    operations = [
        migrations.RenameField(
            model_name='displayproduct',
            old_name='enabaled',
            new_name='enabled',
        ),
        migrations.RunPython(remove_null_records_in_displayproduct),
        migrations.RunPython(remove_null_records_in_featureversion),
        migrations.RunPython(remove_null_records_in_product),
        migrations.RunPython(remove_null_records_in_productplan),
        migrations.AddField(
            model_name='featureversion',
            name='detail',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='type',
            field=models.CharField(default='', max_length=50, blank=True, choices=[(b'NEW', 'New'), (b'UPDATE', 'Update')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='featureversion',
            name='bold',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='featureversion',
            name='position',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_plural',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productfeature',
            name='product_category',
            field=models.ForeignKey(related_name='product_features', to='core.ProductCategory'),
        ),
        migrations.AlterField(
            model_name='productplan',
            name='alternate_frequency',
            field=models.CharField(default='', max_length=31, blank=True, choices=[(b'MONTH', b'Month'), (b'YEAR', b'Year')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productplan',
            name='codename',
            field=models.CharField(unique=True, max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')]),
        ),
        migrations.AlterField(
            model_name='productplan',
            name='commitment',
            field=models.CharField(default='', max_length=31, choices=[(b'MONTH', b'Month'), (b'YEAR', b'Year')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productversion',
            name='product_category',
            field=models.ForeignKey(related_name='product_versions', to='core.ProductCategory'),
        ),
    ]
