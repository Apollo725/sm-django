# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_braintreetransaction_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='due_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
