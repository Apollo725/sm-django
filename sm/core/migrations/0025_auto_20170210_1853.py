# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_customer_communication_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default=b'OPEN', max_length=31, choices=[(b'APPROVED', 'Approved'), (b'CANCELLED', 'Cancelled'), (b'DELIVERED', 'Delivered'), (b'INVOICE_SENT', 'Invoice sent'), (b'OPEN', 'Open'), (b'PAID', 'Paid'), (b'REFUNDED', b'Refunded'), (b'RENEWING', b'Renewing')]),
        ),
    ]
