from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.core import response
from coastal.apps.sale.models import SaleOffer
from coastal.apps.payment.utils import sale_payment_info
from coastal.apps.currency.models import Currency


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
