from __future__ import unicode_literals

from django.db import models, migrations

from sm.core.models import SubscriptionPlan


def subscription_data_migration(apps, schema_editor):
    ProductPlan = apps.get_model('core', 'ProductPlan')
    Subscription = apps.get_model('core', 'Subscription')

    for value, text in SubscriptionPlan.choices():
        product_plan = ProductPlan.objects.filter(codename=value).first()
        if not product_plan:
            continue
        Subscription.objects \
            .filter(old_plan=value) \
            .update(plan=product_plan)
        Subscription.objects \
            .filter(old_vendor_plan=value) \
            .update(vendor_plan=product_plan)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_auto_20180611_1215'),
    ]

    operations = [
        migrations.RunPython(
            subscription_data_migration
        ),
    ]
