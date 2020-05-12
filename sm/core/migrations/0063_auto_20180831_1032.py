# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_auto_20180828_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='displayproduct',
            name='display',
            field=models.BooleanField(default=True, help_text='Show this product with current product'),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='enabled',
            field=models.BooleanField(default=True, help_text='Enable buy/upgrade button'),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='highlighted',
            field=models.BooleanField(default=False, help_text='Distinguish product from others'),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='show_small',
            field=models.BooleanField(default=True, help_text='Show additional alternative price'),
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='showcase_alternate',
            field=models.BooleanField(default=True, help_text='Show alternative price and frequency in the big pricing area'),
        ),
    ]
