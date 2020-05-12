# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20171220_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='version',
            field=models.CharField(blank=True, max_length=31, choices=[(b'BASIC', 'Basic version'), (b'BUSINESS', 'Business version'), (b'EDUCATION', 'Education version'), (b'ENTERPRISE', 'Enterprise version'), (b'FREE', 'Free version'), (b'PRO', 'Professional version')]),
        ),
    ]
