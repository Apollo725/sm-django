# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_create_reseller_temp_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisplayProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=50)),
                ('enabaled', models.BooleanField()),
                ('highlighted', models.BooleanField()),
                ('showcase_alternate', models.BooleanField()),
                ('show_small', models.BooleanField()),
            ],
            options={
                'db_table': 'sm_display_product',
            },
        ),
        migrations.CreateModel(
            name='FeatureProductCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bold', models.BooleanField()),
                ('position', models.IntegerField()),
            ],
            options={
                'db_table': 'sm_feature_product_category',
            },
        ),
        migrations.CreateModel(
            name='FeatureVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bold', models.BooleanField()),
                ('position', models.IntegerField()),
            ],
            options={
                'db_table': 'sm_feature_version',
            },
        ),
        migrations.CreateModel(
            name='ProductFeature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('product_categories', models.ManyToManyField(to='core.ProductCategory', through='core.FeatureProductCategory')),
                ('product_category', models.ForeignKey(related_name='+', to='core.ProductCategory')),
            ],
            options={
                'db_table': 'sm_feature',
            },
        ),
        migrations.CreateModel(
            name='ProductPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('toggle_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=150)),
                ('description', models.CharField(max_length=200)),
                ('billing_frequency', models.CharField(max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')])),
                ('alternative_frequency', models.CharField(max_length=31, null=True, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')])),
                ('commitment', models.CharField(max_length=31, choices=[(b'ANNUAL_MONTHLY', b'Annual monthly'), (b'ANNUAL_YEARLY', b'Annual yearly'), (b'FLEXIBLE', b'Flexible'), (b'FLEX_PREPAID', b'Flex prepaid')])),
            ],
            options={
                'db_table': 'sm_plan',
            },
        ),
        migrations.CreateModel(
            name='ProductVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('codename', models.CharField(unique=True, max_length=100, choices=[(b'BASIC', 'Basic version'), (b'BUSINESS', 'Business version'), (b'EDUCATION', 'Education version'), (b'ENTERPRISE', 'Enterprise version'), (b'FREE', 'Free version'), (b'PRO', 'Professional version')])),
                ('name', models.CharField(max_length=100)),
                ('extended_name', models.CharField(max_length=150)),
                ('color_code', models.CharField(max_length=50)),
                ('motto', models.CharField(max_length=200)),
                ('features', models.ManyToManyField(to='core.ProductFeature', through='core.FeatureVersion')),
                ('product_category', models.ForeignKey(related_name='+', to='core.ProductCategory')),
            ],
            options={
                'db_table': 'sm_version',
            },
        ),
        migrations.RenameField(
            model_name='product',
            old_name='version',
            new_name='old_version',
        ),
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='unit_plural',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='productcatalog',
            name='alternate_price',
            field=models.DecimalField(default=Decimal('0'), null=True, max_digits=10, decimal_places=2),
        ),
        migrations.AddField(
            model_name='productcatalog',
            name='minimal_order',
            field=models.DecimalField(default=Decimal('0'), null=True, max_digits=10, decimal_places=2),
        ),
        migrations.AddField(
            model_name='product',
            name='version',
            field=models.ForeignKey(to='core.ProductVersion', null=True),
        ),
        migrations.AddField(
            model_name='productfeature',
            name='versions',
            field=models.ManyToManyField(to='core.ProductVersion', through='core.FeatureVersion'),
        ),
        migrations.AddField(
            model_name='featureversion',
            name='feature',
            field=models.ForeignKey(to='core.ProductFeature'),
        ),
        migrations.AddField(
            model_name='featureversion',
            name='version',
            field=models.ForeignKey(to='core.ProductVersion'),
        ),
        migrations.AddField(
            model_name='featureproductcategory',
            name='feature',
            field=models.ForeignKey(to='core.ProductFeature'),
        ),
        migrations.AddField(
            model_name='featureproductcategory',
            name='product_category',
            field=models.ForeignKey(to='core.ProductCategory'),
        ),
        migrations.AddField(
            model_name='displayproduct',
            name='current_product',
            field=models.ForeignKey(related_name='current', to='core.Product', null=True),
        ),
        migrations.AddField(
            model_name='displayproduct',
            name='default_plan',
            field=models.ForeignKey(to='core.ProductPlan', null=True),
        ),
        migrations.AddField(
            model_name='displayproduct',
            name='displayed_product',
            field=models.ForeignKey(related_name='displayed', to='core.Product', null=True),
        ),
        migrations.AddField(
            model_name='displayproduct',
            name='product_category',
            field=models.ForeignKey(to='core.ProductCategory', null=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='features',
            field=models.ManyToManyField(to='core.ProductFeature', through='core.FeatureProductCategory'),
        ),
        migrations.AlterUniqueTogether(
            name='featureversion',
            unique_together=set([('version', 'feature')]),
        ),
        migrations.AlterUniqueTogether(
            name='featureproductcategory',
            unique_together=set([('product_category', 'feature')]),
        ),
    ]
