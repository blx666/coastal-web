import math
from coastal.apps.rental.models import RentalOrder, RentalOrderDiscount, ApproveEvent
from coastal.api.rental.forms import RentalBookForm, RentalApproveForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.payment.stripe import get_strip_payment_info
from coastal.api.product.utils import calc_price
from coastal.api.core.decorators import login_required
from coastal.apps.account.utils import is_confirmed_user


@login_required
def book_rental(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    if not is_confirmed_user(request.user):
        return CoastalJsonResponse(status=response.STATUS_1101)
    data = request.POST.copy()
    if 'product_id' in data:
        data['product'] = data.get('product_id')
    form = RentalBookForm(data)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    product = form.cleaned_data.get('product')
    if product.is_no_one:
        status = 'charge'
    else:
        status = 'request'

    rental_order = form.save(commit=False)
    rental_order.status = status
    # TODO: validate the date
    rental_order.product = product
    rental_order.guest = request.user
    rental_order.owner = product.owner

    sub_total_price, total_price, discount_type, discount_rate = \
        calc_price(product, rental_order.rental_unit, rental_order.start_datetime, rental_order.end_datetime)

    rental_order.total_price = total_price
    rental_order.sub_total_price = sub_total_price
    rental_order.currency = product.currency
    # TODO: get currency_rate according to currency
    rental_order.currency_rate = 1
    rental_order.total_price_usd = math.floor(rental_order.total_price / rental_order.currency_rate)
    # rental_order.timezone = product.timezone
    rental_order.save()
    # TODO: move generate order number into save function
    rental_order.number = str(100000+rental_order.id)
    rental_order.save()

    if discount_type and discount_rate:
        RentalOrderDiscount.objects.create(rental_order=rental_order, discount_rate=discount_rate, discount_type=discount_type)
    result = {
        'rental_order_id': rental_order.id,
        'status': rental_order.status,
    }

    if rental_order.status == 'charge':
        if rental_order.total_price_usd < request.user.coastalbucket.balance:
            result['payment_list'] = ['coastal', 'stripe']
            result['coastal'] = {
                'coastal_dollar': request.user.coastalbucket.balance,
                'amount': rental_order.total_price_usd,
            }
        else:
            result['payment_list'] = ['stripe']

        result['stripe'] = get_strip_payment_info(rental_order.total_price, rental_order.currency)

    return CoastalJsonResponse(result)


@login_required
def rental_approve(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        rental_order = RentalOrder.objects.get(owner=request.user, id=request.POST.get('rental_order_id'))
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    if rental_order.status != 'request':
        return CoastalJsonResponse({'status': rental_order.status})

    form = RentalApproveForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    approve = form.cleaned_data.get('approve')
    note = form.cleaned_data.get('note')

    ApproveEvent.objects.create(order=rental_order, notes=note, approve=approve)

    if approve:
        rental_order.status = 'charge'
    else:
        rental_order.status = 'declined'
    rental_order.save()

    result = {
        'status': rental_order.status
    }

    if rental_order.status == 'charge':
        if rental_order.total_price_usd < request.user.coastalbucket.balance:
            result['payment_list'] = ['coastal', 'stripe']
            result['coastal'] = {
                'coastal_dollar': request.user.coastalbucket.balance,
                'amount': rental_order.total_price_usd,
            }
        else:
            result['payment_list'] = ['stripe']

        result['stripe'] = get_strip_payment_info(rental_order.total_price, rental_order.currency)

    return CoastalJsonResponse(result)


@login_required
def payment_stripe(request):
    """
    :param request: POST data {"rental_order_id": 1, "card_id": "card_19UiVAIwZ8ZTWo9bYTC4hguE"}
    :return: json data {}
    """
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        rental_order = RentalOrder.objects.get(guest=request.user, id=request.POST.get('rental_order_id'))
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    # TODO: check order status

    card = request.POST.get('card')
    return CoastalJsonResponse()


@login_required
def delete_rental(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    try:
        rental_order = RentalOrder.objects.get(owner=request.user, id=request.POST.get('rental_order_id'))
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)
    rental_order.is_deleted = True
    rental_order.save()
    return CoastalJsonResponse()
