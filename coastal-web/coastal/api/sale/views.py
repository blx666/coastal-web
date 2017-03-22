import math
from django.utils import timezone

from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.core import response
from coastal.apps.sale.models import SaleOffer, SaleApproveEvent
from coastal.apps.payment.utils import sale_payment_info
from coastal.apps.currency.utils import get_exchange_rate
from coastal.api.sale.forms import SaleOfferForm, SaleApproveForm
from coastal.apps.payment.stripe import sale_charge as stripe_charge
from coastal.apps.payment.coastal import sale_charge as coastal_charge
from coastal.apps.account.models import CoastalBucket, Transaction
from coastal.apps.sns.utils import publish_new_offer, publish_confirmed_offer, publish_refuse_offer, \
    publish_paid_owner_offer
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint
from coastal.apps.sale.tasks import expire_offer_request, expire_offer_charge
from coastal.api import defines as api_defs
from coastal.apps.support.tasks import send_transaction_email


@login_required
def approve(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    try:
        sale_offer = SaleOffer.objects.get(id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    form = SaleApproveForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    _approve = form.cleaned_data.get('approve')
    note = form.cleaned_data.get('note')
    SaleApproveEvent.objects.create(sale_offer=sale_offer, approve=_approve, notes=note)

    if _approve:
        sale_offer.status = 'charge'
        expire_offer_charge.apply_async((sale_offer.id,), countdown=api_defs.EXPIRATION_TIME * 60 * 60)
        try:
            publish_confirmed_offer(sale_offer)
        except (NoEndpoint, DisabledEndpoint):
            pass
    else:
        sale_offer.status = 'declined'
        publish_refuse_offer(sale_offer)
    sale_offer.save()

    result = {
        'status': sale_offer.get_status_display(),
        'sale_offer_id': sale_offer.id,
    }
    result.update(sale_payment_info(sale_offer, request.user))
    return CoastalJsonResponse(result)


@login_required
def sale_detail(request):
    if request.method != 'GET':
        return CoastalJsonResponse(status=response.STATUS_405)
    try:
        sale_offer = SaleOffer.objects.get(id=request.GET.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    result = {
        'owner': sale_offer.owner.basic_info(),
        'guest': sale_offer.guest.basic_info(),
        'product': {
            'id': sale_offer.product.id,
            'name': sale_offer.product.name,
            'for_rental': sale_offer.product.for_rental,
            'for_sale': sale_offer.product.for_sale,
        },
        'sale_price': sale_offer.product.sale_price,
        'sale_price_display': sale_offer.product.get_sale_price_display(),
        'offer_price': sale_offer.price,
        'offer_price_display': sale_offer.get_price_display(),
        'conditions': sale_offer.get_condition_list(),
        'status': sale_offer.get_status_display(),
    }
    result.update(sale_payment_info(sale_offer, sale_offer.guest))
    return CoastalJsonResponse(result)


@login_required
def make_offer(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    data = request.POST.copy()
    if 'product_id' in data:
        data['product'] = data.get('product_id')
    if 'offer_price' in data:
        data['price'] = data.get('offer_price')
    form = SaleOfferForm(data)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    product = form.cleaned_data.get('product')
    if product.status != 'published':
        return CoastalJsonResponse(form.errors, status=response.STATUS_1301)
    sale_offer = form.save(commit=False)

    sale_offer.status = 'request'
    sale_offer.owner = product.owner
    sale_offer.guest = request.user
    sale_offer.currency = product.currency
    sale_offer.currency_rate = get_exchange_rate(sale_offer.currency)
    sale_offer.price_usd = math.ceil(sale_offer.price / sale_offer.currency_rate)
    sale_offer.timezone = product.timezone
    sale_offer.save()
    sale_offer.number = 'SO%s' % (100000 + sale_offer.id)
    sale_offer.save()

    result = {
        "sale_offer_id": sale_offer.id,
        "status": sale_offer.get_status_display(),
    }

    expire_offer_request.apply_async((sale_offer.id,), countdown=api_defs.EXPIRATION_TIME * 60 * 60)
    try:
        publish_new_offer(sale_offer)
    except (NoEndpoint, DisabledEndpoint):
        pass

    return CoastalJsonResponse(result)


@login_required
def delete_offer(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        sale_offer = SaleOffer.objects.get(id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    sale_offer.is_deleted = True
    sale_offer.save()

    return CoastalJsonResponse()


@login_required
def payment_stripe(request):
    """
    :param request: POST data {"sale_offer_id": 1, "card_id": "card_19UiVAIwZ8ZTWo9bYTC4hguE"}
    :return: json data {}
    """
    CHARGED_STATUS_LIST = ('pay', 'finished')

    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        sale_offer = SaleOffer.objects.get(guest=request.user, id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    if sale_offer.status in CHARGED_STATUS_LIST:
        return CoastalJsonResponse(status=response.STATUS_1500)

    if sale_offer.status != 'charge':
        return CoastalJsonResponse({'order': 'The order status should be Unpaid'}, status=response.STATUS_405)

    card = request.POST.get('card_id')
    if not card:
        return CoastalJsonResponse({"card_id": "It is required."}, status=response.STATUS_400)

    success = stripe_charge(sale_offer, request.user, card)
    if success:
        owner = sale_offer.owner
        bucket = CoastalBucket.objects.get(user=owner)
        bucket.balance += sale_offer.price_usd
        bucket.save()
        Transaction.objects.create(
            bucket=bucket,
            type='in',
            order_number=sale_offer.number,
            amount=sale_offer.price_usd,
        )
        sale_offer.status = 'finished'
        sale_offer.date_succeed = timezone.now()
        send_transaction_email(sale_offer.product_id, sale_offer.id, 'sale')
        sale_offer.save()

        try:
            publish_paid_owner_offer(sale_offer)
        except (NoEndpoint, DisabledEndpoint):
            pass

    return CoastalJsonResponse({
        "payment": success and 'success' or 'failed',
        "status": sale_offer.get_status_display(),
    })


@login_required
def payment_coastal(request):
    """
    :param request: POST data {"sale_offer_id": 1}
    :return: json data {}
    """
    CHARGED_STATUS_LIST = ('pay', 'finished')

    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        sale_offer = SaleOffer.objects.get(guest=request.user, id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    if sale_offer.status in CHARGED_STATUS_LIST:
        return CoastalJsonResponse(status=response.STATUS_1500)

    if sale_offer.status != 'charge':
        return CoastalJsonResponse({'order': 'The order status should be Unpaid'}, status=response.STATUS_405)

    sale_offer.currency = sale_offer.product.currency
    sale_offer.currency_rate = get_exchange_rate(sale_offer.currency)
    sale_offer.price_usd = math.ceil(sale_offer.price / sale_offer.currency_rate)
    sale_offer.save()

    success = coastal_charge(sale_offer, request.user)
    if success:
        owner = sale_offer.owner
        bucket = CoastalBucket.objects.get(user=owner)
        bucket.balance += sale_offer.price_usd
        bucket.save()
        Transaction.objects.create(
            bucket=bucket,
            type='in',
            order_number=sale_offer.number,
            amount=sale_offer.price_usd,
        )
        sale_offer.status = 'finished'
        sale_offer.date_succeed = timezone.now()
        send_transaction_email(sale_offer.product_id, sale_offer.id, 'sale')
        sale_offer.save()

        try:
            publish_paid_owner_offer(sale_offer)
        except (NoEndpoint, DisabledEndpoint):
            pass

    return CoastalJsonResponse({
        "payment": success and 'success' or 'failed',
        "status": sale_offer.get_status_display(),
    })
