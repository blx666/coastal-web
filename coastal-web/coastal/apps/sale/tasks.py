from celery import shared_task
from coastal.apps.sale.models import SaleOffer
from coastal.apps.rental.utils import clean_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_order, publish_check_in_order
from coastal.apps.product.models import ProductImage
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint


@shared_task
def expire_offer_request(offer_id):
    try:
        offer = SaleOffer.objects.get(id=offer_id)
    except SaleOffer.DoesNotExist:
        # TODO: add log
        return

    if offer.status == 'request':
        offer.status = 'invalid'
        offer.save()
        clean_rental_out_date(offer.product, offer.start_datetime, offer.end_datetime)
        # TODO: send notification
        try:
            message = 'The offer has been cancelled, for the host didn\'t confirm in 24 hours.'
            product_image = ProductImage.objects.filter(product=offer.product).order_by('display_order').first()
            extra_attr = {
                'type': 'unconfirmed_offer',
                'product_name': offer.product.name,
                'product_image': product_image.image.url
            }

            publish_unconfirmed_order(offer, message, extra_attr)
        except (NoEndpoint, DisabledEndpoint):
            pass


@shared_task
def expire_offer_charge(offer_id):
    try:
        offer = SaleOffer.objects.get(id=offer_id)
    except SaleOffer.DoesNotExist:
        # TODO: add log
        return

    if offer.status == 'charge':
        offer.status = 'invalid'
        offer.save()
        clean_rental_out_date(offer.product, offer.start_datetime, offer.end_datetime)
        # TODO: send notification
        try:
            message = 'Coastal has cancelled the offer for you, for the guest hasn\'t finished ' \
                      'the payment in 24 hours.'
            product_image = ProductImage.objects.filter(product=offer.product).order_by('display_order').first()
            extra_attr = {
                'type': 'unpay_offer',
                'product_name': offer.product.name,
                'product_image': product_image.image.url
            }

            publish_unpay_order(offer, message, extra_attr)
        except (NoEndpoint, DisabledEndpoint):
            pass


@shared_task
def check_in(offer_id):
    try:
        offer = SaleOffer.objects.get(id=offer_id)
    except SaleOffer.DoesNotExist:
        # TODO: add log
        return

    if offer.status == 'booked':
        offer.status = 'check_in'
        offer.save()

        pay_owner.apply_async((offer_id,), countdown=3 * 60 * 60)



@shared_task
def pay_owner(offer_id):
    try:
        offer = SaleOffer.objects.get(id=offer_id)
    except SaleOffer.DoesNotExist:
        # TODO: add log
        return

    if offer.status == 'check-in':
        # TODO: pay owner coastal dollar

        offer.status = 'paid'
        offer.save()

        try:
            message = 'Congratulations! You sold your listing %s, and you have earned %s ' % (offer.product.name, offer.coastal_dollar)
            extra_attr = {
                'type': 'check_in_offer',
                'product_name': offer.product.name,
                'coastal_dollar': offer.coastal_dollar
            }

            publish_check_in_order(offer, message, extra_attr)
        except (NoEndpoint, DisabledEndpoint):
            pass
