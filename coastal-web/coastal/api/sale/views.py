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
        saleoffer = SaleOffer.objects.get(id=request.POST.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    result = {}
    if request.POST.get('approve') == '0':
        result = {
            'status': saleoffer.get_status_display(),
        }
    if request.POST.get('approve') == '1':
        user = saleoffer.guest
        result = {
            'status': saleoffer.status,
        }
        result.update(sale_payment_info(saleoffer, user))
    return CoastalJsonResponse(result)


@login_required
def sale_detail(request):
    if request.method != 'GET':
        return CoastalJsonResponse(status=response.STATUS_405)
    try:
        saleoffer = SaleOffer.objects.get(id=request.GET.get('sale_offer_id'))
    except SaleOffer.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    user = saleoffer.guest
    result = {
        'owner': {
            'id': saleoffer.owner_id,
            'photo': saleoffer.owner.userprofile.photo and saleoffer.owner.userprofile.photo.url or '',
            'name': saleoffer.owner.get_full_name() or '',
        },
        'guest': {
            'id ': saleoffer.guest_id,
            'photo': saleoffer.guest.userprofile.photo and saleoffer.guest.userprofile.photo.url or '',
            'name': saleoffer.owner.get_full_name() or ''
        },
        'sale_price': saleoffer.product.sale_price,
        'sale_price_display': saleoffer.product.get_sale_price_display(),
        'offer_price': saleoffer.price,
        'offer_price_display': '%s%s' % (Currency.objects.get(code=saleoffer.product.currency).display, saleoffer.price),
    }
    result.update(sale_payment_info(saleoffer, user))
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
