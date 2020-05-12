# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_orderdetail_minimal_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('currency', models.CharField(default=b'USD', max_length=10)),
                ('continent', models.CharField(max_length=35)),
                ('trans', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'sm_country',
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('per_user', models.BooleanField()),
                ('customer_type', models.CharField(blank=True, max_length=255, choices=[(b'CUSTOMER', 'Customer'), (b'ECONSULTING_CUSTOMER', 'Econsulting Customer'), (b'ECONSULTING_PARTNER', 'Econsulting Partner'), (b'ECONSULTING_PROSPECT', 'Econsulting Prospect'), (b'ECONSULTING_RESELLER', 'Econsulting Reseller'), (b'EX_RESELLER', 'Ex - Reseller'), (b'GAE_RESELLER', 'GAE Reseller'), (b'GOOGLE_APPS_RESELLER', 'Google Apps Reseller'), (b'PROSPECT', 'Prospect'), (b'RESOLD_CUSTOMER', 'Resold Customer'), (b'RESOLD_PROSPECT', 'Resold Prospect')])),
                ('customer_region', models.CharField(max_length=255, blank=True)),
                ('offline_customer', models.NullBooleanField()),
                ('customer_country', models.CharField(max_length=255, blank=True)),
                ('order_type', models.CharField(max_length=255, blank=True)),
                ('currency', models.CharField(blank=True, max_length=15, choices=[(b'CAD', 'Canadian Dollars'), (b'EUR', 'Euro'), (b'USD', 'American Dollars')])),
                ('vendor_console', models.CharField(blank=True, max_length=255, choices=[(b'canada.gappsexperts.com', 'Canada Gapps'), (b'econsulting.fr', 'EConsulting'), (b'mybonobo.info', 'My bonobo')])),
                ('minimal_quantity', models.IntegerField(null=True, blank=True)),
                ('tax_id', models.CharField(max_length=255, blank=True)),
                ('catalog', models.ForeignKey(blank=True, to='core.Catalog', null=True)),
            ],
            options={
                'db_table': 'sm_policy',
                'verbose_name_plural': 'policies',
            },
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('code', models.CharField(max_length=64, null=True, blank=True)),
                ('parent_category', models.ForeignKey(related_name='child_category', to='core.ProductCategory', null=True)),
            ],
            options={
                'db_table': 'sm_product_category',
            },
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'sm_vendor',
            },
        ),
        migrations.CreateModel(
            name='VendorField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vendor_name', models.CharField(max_length=255)),
                ('sm_name', models.CharField(max_length=255)),
                ('vendor', models.ForeignKey(to='core.Vendor')),
            ],
            options={
                'db_table': 'sm_vendor_fields',
            },
        ),
        migrations.CreateModel(
            name='VendorValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vendor_value', models.CharField(max_length=255)),
                ('sm_value', models.CharField(max_length=255)),
                ('field', models.ForeignKey(to='core.VendorField')),
            ],
            options={
                'db_table': 'sm_vendor_values',
            },
        ),
        migrations.RemoveField(
            model_name='product',
            name='french_name',
        ),
        migrations.RemoveField(
            model_name='product',
            name='list_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='purchase_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='vendor',
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='status',
            field=models.CharField(default=b'OPEN', max_length=31, blank=True, choices=[(b'APPROVED', 'Approved'), (b'CANCELLED', 'Cancelled'), (b'DELIVERED', 'Delivered'), (b'DRAFT', 'Draft'), (b'INVOICE_SENT', 'Invoice sent'), (b'OPEN', 'Open'), (b'PAID', 'Paid'), (b'REFUNDED', b'Refunded'), (b'RENEWING', b'Renewing')]),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='type',
            field=models.CharField(blank=True, max_length=31, choices=[(b'TRANSFER', b'Transfer')]),
        ),
        migrations.AddField(
            model_name='product',
            name='app_url',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='vendor_sku',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='parent_subscription',
            field=models.ForeignKey(related_name='children', blank=True, to='core.Subscription', null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='promotion_banner',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='start_billing_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='unbound',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_commitment_ends',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_commitment_starts',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_console',
            field=models.CharField(blank=True, max_length=255, choices=[(b'canada.gappsexperts.com', 'Canada Gapps'), (b'econsulting.fr', 'EConsulting'), (b'mybonobo.info', 'My bonobo')]),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_customer_id',
            field=models.CharField(max_length=63, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_minimum_transfer',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_trial_ends',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_users',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default=b'OPEN', max_length=31, choices=[(b'APPROVED', 'Approved'), (b'CANCELLED', 'Cancelled'), (b'DELIVERED', 'Delivered'), (b'DRAFT', 'Draft'), (b'INVOICE_SENT', 'Invoice sent'), (b'OPEN', 'Open'), (b'PAID', 'Paid'), (b'REFUNDED', b'Refunded'), (b'RENEWING', b'Renewing')]),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='sub_total',
            field=models.DecimalField(null=True, max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='expiry_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(default=b'ACTIVE', max_length=31, choices=[(b'ACTIVE', 'Active'), (b'DRAFT', 'Draft'), (b'INACTIVE', 'Inactive')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_status',
            field=models.CharField(default=b'EVAL', max_length=31, choices=[(b'ACTIVE', b'ACTIVE'), (b'BILLING_ACTIVATION_PENDING', b'BILLING_ACTIVATION_PENDING'), (b'CANCELLED', b'CANCELLED'), (b'EVAL', b'EVAL'), (b'EXPIRED', b'EXPIRED'), (b'EXPIRED_EVAL', b'EXPIRED_EVAL'), (b'EXPIRED_PAID', b'EXPIRED_PAID'), (b'PAID', b'PAID'), (b'PENDING', b'PENDING'), (b'SUSPENDED', b'SUSPENDED'), (b'UNINSTALLED_EVAL', b'UNINSTALLED_EVAL'), (b'UNINSTALLED_EXPIRED', b'UNINSTALLED_EXPIRED'), (b'UNINSTALLED_PAID', b'UNINSTALLED_PAID')]),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_subscription',
            field=models.CharField(max_length=55, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='vendor',
            field=models.ForeignKey(to='core.Vendor', null=True),
        ),
        migrations.AddField(
            model_name='policy',
            name='product',
            field=models.ForeignKey(blank=True, to='core.Product', null=True),
        ),
        migrations.AddField(
            model_name='policy',
            name='product_category',
            field=models.ForeignKey(to='core.ProductCategory', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=None, to='core.ProductCategory', null=True),
        ),
    ]
