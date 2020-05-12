# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20161121_0624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='braintreetransaction',
            name='order',
            field=models.ForeignKey(related_name='bt_transaction', to='core.Order'),
        ),
    ]
