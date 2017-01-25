from celery import shared_task
from coastal.apps.rental.models import RentalOrder
from coastal.apps.rental.utils import clean_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_order, publish_check_in_order, publish_check_out_order
from coastal.apps.product.models import ProductImage


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
        message = 'The request has been cancelled, for the host didn\'t confirm in 24 hours.'
        product_image = ProductImage.objects.filter(product=order.product).order_by('display_order')[0:1].first()
        extra_attr = {
            'type': 'unconfirmed_order',
            'product_name': order.product.name,
            'product_image': product_image.image.url
        }

        publish_unconfirmed_order(order, message, extra_attr)


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
        message = 'Coastal has cancelled the request for you, for the guest hasn\'t finished ' \
                  'the payment in 24 hours.'
        product_image = ProductImage.objects.filter(product=order.product).order_by('display_order')[0:1].first()
        extra_attr = {
            'type': 'unpay_order',
            'product_name': order.product.name,
            'product_image': product_image.image.url
        }

        publish_unpay_order(order, message, extra_attr)

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
        message = 'Congratulations! You have earned %s ' % (order.coastal_dollar)
        product_image = ProductImage.objects.filter(product=order.product).order_by('display_order')[0:1].first()
        extra_attr = {
            'type': 'check_in_order',
            'product_name': order.product.name,
            'product_image': product_image.image.url
        }

        publish_check_in_order(order, message, extra_attr)


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

        message = 'Please check-out your rental.'
        product_image = ProductImage.objects.filter(product=order.product).order_by('display_order')[0:1].first()
        extra_attr = {
            'type': 'check_out_order',
            'product_name': order.product.name,
            'product_image': product_image.image.url,
            'product_id': order.product.id,
            'rental_order_id': order_id,
        }
        publish_check_out_order(order, message, extra_attr)

        # TODO: send notification
