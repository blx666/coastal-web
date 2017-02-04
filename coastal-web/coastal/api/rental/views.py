import math
import datetime
from django.utils import timezone
from coastal.apps.rental.models import RentalOrder, RentalOrderDiscount, ApproveEvent
from coastal.api.rental.forms import RentalBookForm, RentalApproveForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.payment.utils import get_payment_info
from coastal.apps.payment.stripe import charge as stripe_charge
from coastal.apps.payment.coastal import charge as coastal_charge
from coastal.api.product.utils import calc_price
from coastal.api.core.decorators import login_required
from coastal.apps.product import defines as defs
from coastal.apps.account.utils import is_confirmed_user
from coastal.apps.rental.utils import validate_rental_date, rental_out_date, clean_rental_out_date
from coastal.apps.currency.utils import get_exchange_rate
from coastal.apps.rental.tasks import expire_order_request, expire_order_charge, check_in
from coastal.apps.sns.utils import publish_get_order, publish_confirmed_order, publish_refuse_order, publish_paid_order
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint


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

    rental_order = form.save(commit=False)
    valid = validate_rental_date(product, rental_order.start_datetime, rental_order.end_datetime)
    if valid:
        return CoastalJsonResponse(status=response.STATUS_1300)
    rental_order.owner = product.owner

    if product.is_no_one:
        rental_order.status = 'request'
    else:
        rental_order.status = 'charge'

    rental_order.product = product
    rental_order.guest = request.user

    sub_total_price, total_price, discount_type, discount_rate = \
        calc_price(product, rental_order.rental_unit, rental_order.start_datetime, rental_order.end_datetime)
    rental_order.total_price = total_price
    rental_order.sub_total_price = sub_total_price
    rental_order.currency = product.currency
    rental_order.currency_rate = get_exchange_rate(rental_order.currency)
    rental_order.total_price_usd = math.ceil(rental_order.total_price / rental_order.currency_rate)
    rental_order.timezone = product.timezone
    if product.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT, defs.CATEGORY_ROOM) and rental_order.rental_unit == 'day':
        rental_order.start_datetime += datetime.timedelta(hours=12)
        rental_order.end_datetime -= datetime.timedelta(hours=11, minutes=59, seconds=59)

    rental_order.save()
    if rental_order.status == 'request':
        try:
            publish_get_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass
    rental_out_date(rental_order.product, rental_order.start_datetime, rental_order.end_datetime)
    # TODO: move generate order number into save function
    rental_order.number = 'RO%s' % (100000 + rental_order.id)
    rental_order.save()

    if discount_type and discount_rate:
        RentalOrderDiscount.objects.create(rental_order=rental_order, discount_rate=discount_rate, discount_type=discount_type)
    result = {
        'rental_order_id': rental_order.id,
        'status': rental_order.get_status_display(),
    }

    if rental_order.status == 'charge':
        result.update(get_payment_info(rental_order, request.user))
        expire_order_charge.apply_async((rental_order.id,), countdown=60 * 60)

    if rental_order.status == 'request':
        try:
            publish_get_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass
        expire_order_request.apply_async((rental_order.id,), countdown=24 * 60 * 60)

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
        rental_order.save()
        try:
            publish_confirmed_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass
    else:
        rental_order.status = 'declined'
        rental_order.save()
        clean_rental_out_date(rental_order.product, rental_order.start_datetime,rental_order.end_datetime)
        try:
            publish_refuse_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass

    result = {
        'status': rental_order.get_status_display(),
        'rental_order_id': rental_order.id,
    }

    if rental_order.status == 'charge':
        result.update(get_payment_info(rental_order, request.user))
        expire_order_charge.apply_async((rental_order.id,), countdown=24 * 60 * 60)

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

    if success:
        rental_order.status = 'booked'
        rental_order.save()

        check_in.apply_async((rental_order.id,), eta=rental_order.start_datetime)
        try:
            publish_paid_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass

    return CoastalJsonResponse({
        "payment": success and 'success' or 'failed',
        "status": rental_order.get_status_display(),
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

    if success:
        rental_order.coastal_dollar = rental_order.total_price_usd
        rental_order.status = 'booked'
        rental_order.save()

        check_in.apply_async((rental_order.id,), eta=rental_order.start_datetime)
        try:
            publish_paid_order(rental_order)
        except (NoEndpoint, DisabledEndpoint):
            pass

    return CoastalJsonResponse({
        "payment": success and 'success' or 'failed',
        "status": rental_order.get_status_display(),
    })


@login_required
def order_detail(request):
    try:
        order = RentalOrder.objects.get(id=request.GET.get('rental_order_id'))
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)

    start_time = order.start_datetime
    end_time = order.end_datetime

    time_format = order.rental_unit == 'day' and '%A/ %B %d, %Y' or '%l:%M %p, %A/ %B %d, %Y'
    start_datetime = timezone.localtime(start_time, timezone.get_current_timezone()).strftime(time_format)
    end_datetime = timezone.localtime(end_time, timezone.get_current_timezone()).strftime(time_format)

    result = {
        'title': 'Book %s at %s' % (order.get_time_length_display(), order.product.city.title()),
        'product': {
            'category': order.product.category_id,
            'for_rental': order.product.for_rental,
            'for_sale': order.product.for_sale,
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
            'name': order.owner.get_full_name() or order.owner.email,
        },
        'guest': {
            'id': order.guest.id,
            'photo': order.guest.userprofile.photo and order.guest.userprofile.photo.url or '',
            'name': order.guest.get_full_name() or order.guest.email,
        },
        'guests': order.guest_count,
        'start_date': start_datetime,
        'end_date': end_datetime,
        'total_price_display': order.get_total_price_display(),
        'status': order.get_status_display(),
    }

    if order.status == 'charge':
        result.update(get_payment_info(order, request.user))
    return CoastalJsonResponse(result)


@login_required
def delete_order(request):
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
