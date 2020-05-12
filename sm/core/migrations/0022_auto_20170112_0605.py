# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20170112_0502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='type',
            field=models.CharField(default=b'PROSPECT', max_length=31, choices=[(b'CUSTOMER', 'Customer'), (b'ECONSULTING_CUSTOMER', 'Econsulting Customer'), (b'ECONSULTING_PARTNER', 'Econsulting Partner'), (b'ECONSULTING_PROSPECT', 'Econsulting Prospect'), (b'EX_RESELLER', 'Ex - Reseller'), (b'GAE_RESELLER', 'GAE Reseller'), (b'GOOGLE_APPS_RESELLER', 'Google Apps Reseller'), (b'PROSPECT', 'Prospect'), (b'RESOLD_CUSTOMER', 'Resold Customer'), (b'RESOLD_PROSPECT', 'Resold Prospect')]),
        ),
    ]
