# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from sm.core.models import SubscriptionPlan


def migrate_product_plan(apps, schema_editor):
    ProductPlan = apps.get_model('core', 'ProductPlan')
    Product = apps.get_model('core', 'Product')

    for plan in SubscriptionPlan:
        products = Product.objects.filter(old_plan=plan.value)
        try:
            product_plan = ProductPlan.objects.get(codename=plan.value)
        except ProductPlan.DoesNotExist:
            continue

        products.update(plan=product_plan)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_auto_20180523_1321'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='plan',
            new_name='old_plan',
        ),
        migrations.AddField(
            model_name='product',
            name='plan',
            field=models.ForeignKey(related_name='products', to='core.ProductPlan', null=True),
        ),
        migrations.AddField(
            model_name='productplan',
            name='codename',
            field=models.CharField(default=None, max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productplan',
            name='alternate_frequency',
            field=models.CharField(max_length=31, null=True, choices=[(b'MONTH', b'Month'), (b'YEAR', b'Year')]),
        ),
        migrations.AlterField(
            model_name='productplan',
            name='billing_frequency',
            field=models.CharField(max_length=31, choices=[(b'MONTH', b'Month'), (b'YEAR', b'Year')]),
        ),
        migrations.AlterField(
            model_name='productplan',
            name='commitment',
            field=models.CharField(max_length=31, null=True, choices=[(b'MONTH', b'Month'), (b'YEAR', b'Year')]),
        ),
        migrations.RunPython(migrate_product_plan),
        migrations.RemoveField(
            model_name='product',
            name='old_plan',
        ),
    ]
