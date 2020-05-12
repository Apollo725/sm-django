# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def fix_update_to_upgrade(apps, schema_editor):
    DisplayProduct = apps.get_model('core', 'DisplayProduct')
    DisplayProduct.objects.filter(type='UPDATE').update(type='UPGRADE')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0058_auto_20180625_0741'),
    ]

    operations = [
        migrations.RunPython(
            fix_update_to_upgrade
        ),
        migrations.AddField(
            model_name='subscription',
            name='upgrade_order',
            field=models.CharField(default='EXTEND', max_length=6, choices=[(b'EXTEND', 'Extend'), (b'REFUND', 'Refund')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='displayproduct',
            name='type',
            field=models.CharField(blank=True, max_length=50, choices=[(b'ADD', 'Add'), (b'NEW', 'New'), (b'UPGRADE', 'Upgrade')]),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='type',
            field=models.CharField(blank=True, max_length=31, choices=[(b'ADD', 'Add'), (b'NEW', 'New'), (b'REFUND', 'Refund'), (b'TRANSFER', b'Transfer'), (b'UPGRADE', 'Upgrade')]),
        ),

    ]
