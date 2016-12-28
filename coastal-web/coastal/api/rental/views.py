from coastal.apps.rental.models import RentalOrder
from coastal.api.rental.forms import RentalBookForm, RentalApproveForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product
from coastal.api.product.views import calc_price


def book_rental(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    form = RentalBookForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    product_id = form.cleaned_data['product_id']
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
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
    rental_order.sub_total_price = calc_price(product, rental_order.start_datetime, rental_order.end_datetime)
    rental_order.currency = product.currency
    discount_weekly = product.discount_weekly
    discount_monthly = product.discount_monthly
    timedelta = (rental_order.end_datetime-rental_order.start_datetime).days
    if timedelta >= 30 and discount_monthly:
        rental_order.total_price = rental_order.sub_total_price * discount_monthly / 100
    elif timedelta >= 7 and discount_weekly:
        rental_order.total_price = rental_order.sub_total_price * discount_weekly / 100
    else:
        rental_order.total_price = rental_order.sub_total_price
    # rental_order.timezone = product.timezone
    rental_order.save()
    rental_order.number = str(100000+rental_order.id)
    rental_order.save()
    result = {
        'rental_order_id': rental_order.id,
        'status': rental_order.status,
    }
    return CoastalJsonResponse(result)


def rental_approve(request, rental_order_id):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    form = RentalApproveForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    try:
        rental_order = RentalOrder.objects.get(id=rental_order_id)
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    approve = form.cleaned_data.get('approve')
    note = form.cleaned_data.get('note')
    if approve:
        rental_order.status = 'approved'
    else:
        rental_order.status = 'declined'
    rental_order.save()
    result ={
        'status': rental_order.status
    }
    return CoastalJsonResponse(result)
