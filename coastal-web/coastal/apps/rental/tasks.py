from celery import shared_task
from coastal.apps.rental.models import RentalOrder
from coastal.apps.rental.utils import clean_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_order, publish_paid_owner_order, \
    publish_check_out_order
from coastal.apps.product.models import ProductImage
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
        clean_rental_out_date(order.product, order.start_datetime, order.end_datetime)
        # TODO: send notification
        try:
            message = 'The request has been cancelled, for the host didn\'t confirm in 24 hours.'
            product_image = ProductImage.objects.filter(product=order.product).order_by('display_order').first()
            extra_attr = {
                'type': 'unconfirmed_order',
                'product_name': order.product.name,
                'product_image': product_image.image.url
            }

            publish_unconfirmed_order(order, message, extra_attr)
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
        clean_rental_out_date(order.product, order.start_datetime, order.end_datetime)
        # TODO: send notification
        try:
            message = 'Coastal has cancelled the request for you, for the guest hasn\'t finished ' \
                      'the payment in 24 hours.'
            product_image = ProductImage.objects.filter(product=order.product).order_by('display_order').first()
            extra_attr = {
                'type': 'unpay_order',
                'product_name': order.product.name,
                'product_image': product_image.image.url
            }

            publish_unpay_order(order, message, extra_attr)
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
        order.status = 'check_in'
        order.save()

        pay_owner.apply_async((order_id,), countdown=3 * 60 * 60)



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

    if order.status == 'paid':
        order.status = 'finished'
        order.save()

        try:
            publish_check_out_order(order)
        except (NoEndpoint, DisabledEndpoint):
            pass
