# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_auto_20180608_1211'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='plan',
            new_name='old_plan',
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='vendor_plan',
            new_name='old_vendor_plan',
        ),
        migrations.AddField(
            model_name='subscription',
            name='plan',
            field=models.ForeignKey(null=True, related_name='subscriptions', to='core.ProductPlan'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='vendor_plan',
            field=models.ForeignKey(null=True, related_name='vendor_subscription_set', to='core.ProductPlan'),
        ),
    ]
