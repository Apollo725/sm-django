# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_product_version_data_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productversion',
            name='codename',
            field=models.CharField(unique=True, max_length=100, choices=[(b'BASIC', 'Basic version'), (b'BUSINESS', 'Business version'), (b'EDUCATION', 'Education version'), (b'ENTERPRISE', 'Enterprise version'), (b'EVALUATION', 'Evaluation version'), (b'FREE', 'Free version'), (b'PRO', 'Professional version')]),
        ),
        migrations.RenameField(
            model_name='productplan',
            old_name='alternative_frequency',
            new_name='alternate_frequency',
        )
    ]
