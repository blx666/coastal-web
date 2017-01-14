from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.core import response
from coastal.apps.sale.models import SaleOffer
from coastal.apps.payment.utils import sale_payment_info
from coastal.apps.currency.models import Currency
from coastal.apps.account.utils import is_confirmed_user
from coastal.api.sale.forms import SaleOfferForm


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

    result = {}
    if request.POST.get('approve') == '0':
        result = {
            'status': sale_offer.get_status_display(),
        }
    if request.POST.get('approve') == '1':
        user = sale_offer.guest
        result = {
            'status': sale_offer.status,
        }
        result.update(sale_payment_info(sale_offer, user))
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
    }
    result.update(sale_payment_info(sale_offer, user))
    return CoastalJsonResponse(result)


# @login_required
def make_offer(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    # if not is_confirmed_user(request.user):
    #     return CoastalJsonResponse(status=response.STATUS_1101)
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
