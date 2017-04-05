from celery import shared_task
from coastal.apps.account.models import CoastalBucket, Transaction
from coastal.apps.rental.models import RentalOrder
from coastal.apps.rental.utils import clean_rental_out_date, recreate_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_order, publish_paid_owner_order, \
    publish_check_out_order
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint


@shared_task
def expire_order_request(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'request':
        order.status = 'invalid'
        order.save()
        recreate_rental_out_date(order.product)
        try:
            publish_unconfirmed_order(order)
        except (NoEndpoint, DisabledEndpoint):
            pass


@shared_task
def expire_order_charge(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'charge':
        order.status = 'invalid'
        order.save()
        recreate_rental_out_date(order.product)
        try:
            publish_unpay_order(order)
        except (NoEndpoint, DisabledEndpoint):
            pass


@shared_task
def check_in(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'booked':
        order.status = 'check-in'
        order.save()

        pay_owner.apply_async((order.id,), countdown=3 * 60 * 60)
        check_out.apply_async((order.id,), eta=order.local_end_datetime)


@shared_task
def pay_owner(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status in ('check-in', 'check-out'):
        bucket = CoastalBucket.objects.get(user=order.owner)
        bucket.balance += order.total_price_usd
        bucket.save()
        Transaction.objects.create(
            bucket=bucket,
            type='in',
            order_number=order.number,
            amount=order.total_price_usd,
        )

        if order.status == 'check-in':
            order.status = 'paid'
            order.save()

        if order.status == 'check-out':
            order.status = 'finished'
            order.save()

        try:
            publish_paid_owner_order(order)
        except (NoEndpoint, DisabledEndpoint):
            pass


@shared_task
def check_out(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status in ('check-in', 'paid'):
        if order.status == 'check-in':
            order.status = 'check-out'
            order.save()

        if order.status == 'paid':
            order.status = 'finished'
            order.save()

        try:
            publish_check_out_order(order)
        except (NoEndpoint, DisabledEndpoint):
            pass
