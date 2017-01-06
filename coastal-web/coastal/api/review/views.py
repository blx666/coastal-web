from coastal.apps.review.models import Review
from coastal.api.review.forms import ReviewForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse


def write_review(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    data = request.POST.copy()
    if 'order_id' in data:
        data['order'] = data.get('order_id')
    form = ReviewForm(data)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    order = form.cleaned_data['order']
    content = form.cleaned_data['content']
    score = form.cleaned_data['score']
    owner = request.user
    product = order.product
    if order.status not in ('check-out', 'finished'):
        return CoastalJsonResponse('This order cannot review')
    Review.objects.update_or_create(order=order, product=product, owner=owner, score=score, content=content)
    return CoastalJsonResponse()
