# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_auto_20180729_1053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='vendor_commitment_ends',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_commitment_starts',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_trial_ends',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='vendor_users',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
