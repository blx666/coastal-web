import math

from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.core import response
from coastal.apps.sale.models import SaleOffer, SaleApproveEvent, SalePaymentEvent
from coastal.apps.payment.utils import sale_payment_info
from coastal.apps.currency.models import Currency
from coastal.apps.account.utils import is_confirmed_user
from coastal.apps.currency.utils import get_exchange_rate
from coastal.api.sale.forms import SaleOfferForm, SaleApproveForm
from coastal.apps.payment.stripe import sale_charge as stripe_charge
from coastal.apps.payment.coastal import sale_charge as coastal_charge
from coastal.apps.account.models import CoastalBucket, Transaction


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

    approve = form.cleaned_data.get('approve')
    note = form.cleaned_data.get('note')
    SaleApproveEvent.objects.create(sale_offer=sale_offer, approve=approve, notes=note)

    if approve:
        sale_offer.status = 'charge'
    else:
        sale_offer.status = 'declined'
    sale_offer.save()

    result = {
        'status': sale_offer.get_status_display(),
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

    user = sale_offer.guest
    result = {
        'owner': {
            'id': sale_offer.owner_id,
            'photo': sale_offer.owner.userprofile.photo and sale_offer.owner.userprofile.photo.url or '',
            'name': sale_offer.owner.get_full_name() or '',
        },
        'guest': {
            'id ': sale_offer.guest_id,
            'photo': sale_offer.guest.userprofile.photo and sale_offer.guest.userprofile.photo.url or '',
            'name': sale_offer.owner.get_full_name() or ''
        },
        'sale_price': sale_offer.product.sale_price,
        'sale_price_display': sale_offer.product.get_sale_price_display(),
        'offer_price': sale_offer.price,
        'offer_price_display': sale_offer.get_price_display(),
        'conditions': sale_offer.get_condition_list(),
        'status': sale_offer.get_status_display(),
    }
    result.update(sale_payment_info(sale_offer, user))
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
    sale_offer = form.save(commit=False)
    sale_offer.status = 'request'
    sale_offer.owner = product.owner
    sale_offer.guest = request.user
    sale_offer.currency = product.currency
    sale_offer.currency_rate = get_exchange_rate(sale_offer.currency)
    sale_offer.price_usd = math.ceil(sale_offer.price / sale_offer.currency_rate)
    sale_offer.timezone = product.timezone
    sale_offer.save()
    sale_offer.number = str(100000+sale_offer.id)
    sale_offer.save()
    result = {
        "sale_offer_id": sale_offer.id,
        "status": sale_offer.get_status_display(),
    }
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
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        sale_offer = SaleOffer.objects.get(guest=request.user, id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

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
            order_number=sale_offer.number
        )
        sale_offer.status = 'finished'
        sale_offer.save()

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
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        sale_offer = SaleOffer.objects.get(guest=request.user, id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

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
            order_number=sale_offer.number
        )
        sale_offer.status = 'finished'
        sale_offer.save()

    return CoastalJsonResponse({
        "payment": success and 'success' or 'failed',
        "status": sale_offer.get_status_display(),
    })
