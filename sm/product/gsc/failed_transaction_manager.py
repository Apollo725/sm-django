from django.utils import timezone
from .models import FailedTransaction, ZohoCustomerRecord


def create(order, error):
    customer = order.customer
    # always use the converted potential for the first payment
    potential_id = None
    if customer.payment_position <= 1:
        record = ZohoCustomerRecord.objects.filter(customer=customer).first()
        potential_id = record.potential_id if record else None

    if not potential_id:
        potential_id = find_potential_id(order)

    failed_transaction = FailedTransaction.objects.create(
        date=timezone.now(),
        error=error,
        order=order,
        potential_id=potential_id
    )

    return failed_transaction


def find_potential_id(order):
    tx = FailedTransaction.objects.filter(order=order).order_by('-date').first()
    if tx:
        return tx.potential_id
    return None


def update_potential_id(tx, potential_id):
    tx.potential_id = potential_id
    tx.save()
