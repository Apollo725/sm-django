# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('test', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GSCTestUser',
        ),
        migrations.AddField(
            model_name='gsctestdomain',
            name='granted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='gsctestdomain',
            name='registered',
            field=models.BooleanField(default=False),
        ),
    ]
