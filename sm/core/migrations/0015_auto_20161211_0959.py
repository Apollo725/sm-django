# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_subscription_paypal_failure'),
    ]

    operations = [
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='card_type',
            field=models.CharField(max_length=31, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='detail',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='expiration_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='last_4_digits',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='braintreepaymentmethod',
            name='type',
            field=models.CharField(blank=True, max_length=31, null=True, choices=[(b'credit_card', b'Credit Card'), (b'paypal', b'Paypal')]),
        ),
    ]
