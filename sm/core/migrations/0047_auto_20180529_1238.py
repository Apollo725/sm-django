# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_productversion_sku'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultProductPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('users_limit', models.IntegerField()),
                ('current_product', models.ForeignKey(to='core.Product')),
                ('plan', models.ForeignKey(to='core.ProductPlan')),
            ],
            options={
                'db_table': 'sm_default_product_plan',
            },
        ),
        migrations.RemoveField(
            model_name='displayproduct',
            name='default_plan',
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='current_product',
            field=models.ForeignKey(related_name='current', to='core.Product'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='displayed_product',
            field=models.ForeignKey(related_name='displayed', to='core.Product'),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='type',
            field=models.CharField(max_length=50, choices=[(b'NEW', 'New'), (b'UPDATE', 'Update')]),
        ),
    ]
