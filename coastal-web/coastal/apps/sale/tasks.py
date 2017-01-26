from celery import shared_task
from coastal.apps.sale.models import SaleOffer
from coastal.apps.rental.utils import clean_rental_out_date
from coastal.apps.sns.utils import publish_unconfirmed_order, publish_unpay_offer
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

        try:
            publish_unconfirmed_order(offer)
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

        try:
            publish_unpay_offer(offer)
        except (NoEndpoint, DisabledEndpoint):
            pass
