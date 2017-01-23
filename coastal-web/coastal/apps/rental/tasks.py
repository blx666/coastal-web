from celery import shared_task
from coastal.apps.rental.models import RentalOrder
from coastal.apps.rental.utils import clean_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_order, publish_check_in_order, publish_check_out_order


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
        clean_rental_out_date(order.product, order.start_datetime, order.end_datetime)
        publish_unconfirmed_order(order)


        # TODO: send notification


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
        clean_rental_out_date(order.product, order.start_datetime, order.end_datetime)
        # TODO: send notification
        publish_unpay_order(order)

@shared_task
def check_in(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'booked':
        order.status = 'check_in'
        order.save()

        pay_owner.apply_async((order_id,), countdown=3 * 60 * 60)
        publish_check_in_order(order)


@shared_task
def pay_owner(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'check-in':
        # TODO: pay owner coastal dollar

        order.status = 'paid'
        order.save()

        # TODO: send notification


@shared_task
def check_out(order_id):
    try:
        order = RentalOrder.objects.get(id=order_id)
    except RentalOrder.DoesNotExist:
        # TODO: add log
        return

    if order.status == 'paid':
        order.status = 'finished'
        order.save()
        publish_check_out_order(order)

        # TODO: send notification
