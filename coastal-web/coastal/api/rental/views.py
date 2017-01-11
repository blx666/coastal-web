import math
from coastal.apps.rental.models import RentalOrder, RentalOrderDiscount, ApproveEvent
from coastal.api.rental.forms import RentalBookForm, RentalApproveForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.currency.utils import get_exchange_rate
from coastal.apps.payment.utils import get_payment_info
from coastal.apps.payment.stripe import charge as stripe_charge
from coastal.apps.payment.coastal import charge as coastal_charge
from coastal.api.product.utils import calc_price
from coastal.api.core.decorators import login_required
from coastal.apps.payment.stripe import get_card_list
from coastal.apps.product import defines as defs
from datetime import datetime
import time
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
        result.update(get_payment_info(rental_order, request.user))

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
        result.update(get_payment_info(rental_order, request.user))

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

    if rental_order.status != 'charge':
        return CoastalJsonResponse({'order': 'The order status should be Unpaid'}, status=response.STATUS_405)

    card = request.POST.get('card')
    if not card:
        return CoastalJsonResponse({"card": "It is required."}, status=response.STATUS_400)

    success = stripe_charge(rental_order, request.user, card)

    return CoastalJsonResponse({
        "paid": success and 'success' or 'failed',
        "status": rental_order.status,
    })


@login_required
def payment_coastal(request):
    """
    :param request: POST data {"rental_order_id": 1}
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

    if rental_order.status != 'charge':
        return CoastalJsonResponse({'order': 'The order status should be Unpaid'}, status=response.STATUS_405)

    rental_order.currency = rental_order.product.currency
    rental_order.currency_rate = get_exchange_rate(rental_order.currency)
    rental_order.total_price_usd = math.ceil(rental_order.total_price / rental_order.currency_rate)
    rental_order.save()

    success = coastal_charge(rental_order, request.user)

    return CoastalJsonResponse({
        "paid": success and 'success' or 'failed',
        "status": rental_order.status,
    })


@login_required
def order_detail(request):
    order = RentalOrder.objects.get(id=request.GET.get('rental_order_id'))
    start_time = order.start_datetime
    end_time = order.end_datetime
    if order.product.rental_unit == 'day':
        start_datetime = datetime.strftime(start_time, '%A/ %B %dst,%Y')
        end_datetime = datetime.strftime(end_time, '%A/ %B %dst,%Y')
    else:
        start_datetime = datetime.strftime(start_time, '%A, %B %dst %H,%Y')
        end_datetime = datetime.strftime(end_time, '%A, %B %dst %H,%Y')

    if order.product.rental_unit == 'day':
        if order.product.category_id in (defs.CATEGORY_BOAT_SLIP, defs.CATEGORY_YACHT):
            time_info = math.ceil(
                (time.mktime(end_time.timetuple()) - time.mktime(start_time.timetuple())) / (3600 * 24)) + 1
        else:
            time_info = math.ceil(
                (time.mktime(end_time.timetuple()) - time.mktime(start_time.timetuple())) / (3600 * 24))
    if order.product.rental_unit == 'half-day':
        time_info = math.ceil((time.mktime(end_time.timetuple()) - time.mktime(start_time.timetuple())) / (3600 * 6))
    if order.product.rental_unit == 'hour':
        time_info = math.ceil((time.mktime(end_time.timetuple()) - time.mktime(start_time.timetuple())) / 3600)
    if time_info > 1:
        title = 'Book %s %ss as %s' % (time_info, order.product.rental_unit.title(), order.product.city.title())
    else:
        title = 'Book %s %s as %s' % (time_info, order.product.rental_unit.title(), order.product.city.title())

    result = {
        'title': title,
        'product': {
            'rooms': order.product.rooms or 0,
            'bathrooms': order.product.bathrooms or 0,
            'beds': order.product.beds or 0,
            'cancel_policy': 'Coastal does not provide online cancellation service. '
                             'Please contact us if you have any needs.',
            'rental_rule': {
                'content': order.product.rental_rule or 'Nothing is set',
                'name': '%s Rules' % order.product.category.name
            },
        },
        'owner': {
            'id': order.owner.id,
            'photo': order.owner.userprofile.photo and order.owner.userprofile.photo.url or '',
            'name': order.owner.get_full_name(),
        },
        'guest': {
            'id': order.guest.id,
            'photo': order.guest.userprofile.photo and order.guest.userprofile.photo.url or '',
            'name': order.guest.get_full_name()
        },
        'guests': order.guest_count,
        'start_date': start_datetime,
        'end_date': end_datetime,
        'total_price_display': order.get_total_price_display(),
        'status': order.get_status_display(),
        'product_unit': order.product.category.name,
    }

    if order.status == 'charge':
        result.update(get_payment_info(order, request.user))
    return CoastalJsonResponse(result)


@login_required
def delete_rental(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        rental_order = RentalOrder.objects.get(id=request.POST.get('rental_order_id'))
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    rental_order.is_deleted = True
    rental_order.save()

    return CoastalJsonResponse()
