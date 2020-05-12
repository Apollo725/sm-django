# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20160328_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='owner',
            field=models.CharField(default=b'', choices=[(b'Braintree GAE', b'Braintree GAE'), (b'Paypal GAE', b'Paypal GAE'), (b'Paypal GSC', b'Paypal GSC'), (b'Paypal EC', b'Paypal EC'), (b'Invoice GAE', b'Invoice GAE'), (b'Invoice EC', b'Invoice EC')], max_length=255, blank=True, null=True, verbose_name=b'Owner'),
        ),
    ]
