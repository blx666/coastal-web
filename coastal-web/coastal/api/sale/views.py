from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.core import response
from coastal.apps.sale.models import SaleOffer
from coastal.apps.payment.utils import sale_payment_info


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
