from coastal.apps.rental.models import RentalOrder, RentalOrderDiscount, ApproveEvent
from coastal.api.rental.forms import RentalBookForm, RentalApproveForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product
from coastal.api.product.utils import calc_price
from coastal.api.core.decorators import login_required


@login_required
def book_rental(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
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
    # rental_order.timezone = product.timezone
    rental_order.save()
    rental_order.number = str(100000+rental_order.id)
    rental_order.save()

    if discount_type and discount_rate:
        RentalOrderDiscount.objects.create(rental_order=rental_order, discount_rate=discount_rate, discount_type=discount_type)
    result = {
        'rental_order_id': rental_order.id,
        'status': rental_order.status,
    }
    return CoastalJsonResponse(result)


@login_required
def rental_approve(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    form = RentalApproveForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    rental_order_id = request.POST.get('rental_order_id')
    try:
        rental_order = RentalOrder.objects.get(id=rental_order_id)
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    approve = form.cleaned_data.get('approve')
    note = form.cleaned_data.get('note')
    if rental_order.status != 'request':
        return CoastalJsonResponse({'status': rental_order.status})
    if approve:
        rental_order.status = 'approved'
    else:
        rental_order.status = 'declined'
    rental_order.save()
    if approve == 0:
        ApproveEvent.objects.create(order=rental_order, notes=note, approve=False)
    if approve == 1:
        ApproveEvent.objects.create(order=rental_order, notes=note, approve=True)
    result = {
        'status': rental_order.status
    }
    return CoastalJsonResponse(result)
