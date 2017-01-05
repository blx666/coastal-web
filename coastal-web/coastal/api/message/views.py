from coastal.apps.message.models import Dialogue
from coastal.api.message.forms import DialogueForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.rental.models import RentalOrder
from django.contrib.gis.db.models import Q
from coastal.api.core.decorators import login_required
import datetime


@login_required
def create_dialogue(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    form = DialogueForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    product_id = form.cleaned_data['product_id']
    product = Product.objects.filter(id=product_id).first()

    if not product:
        return CoastalJsonResponse(status=response.STATUS_404)

    order = RentalOrder.objects.filter(owner=product.owner, guest=request.user,
                                       product=product).first()
    dialogue, _ = Dialogue.objects.update_or_create(owner=product.owner, guest=request.user,
                                                    product=product, order=order)

    result = {
        'dialogue_id': dialogue.id,
    }
    return CoastalJsonResponse(result)


@login_required
def dialogue_list(request):
    dialogues = Dialogue.objects.filter(Q(owner=request.user) | Q(guest=request.user))
    today = datetime.date.today()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    today_list = []
    yesterday_list = []
    past_list = []
    for dialogue in dialogues:
        guest = request.user == dialogue.owner and dialogue.guest or dialogue.owner
        product = dialogue.product
        order = dialogue.order
        guest_dict = {
            'user_id': guest.id,
            'first_name': guest.first_name,
            'last_name': guest.last_name,
            'photo': guest.userprofile.photo.url if guest.userprofile.photo else '',
        }
        product_image = ProductImage.objects.filter(product=product).first()
        product_dict = {
            'product_id': product.id,
            'name': product.name,
            'image': product_image.image.url,
        }
        order_dict = {}
        if order:
            order_dict = {
                'order_id': order.id,
                'status': order.status,
                'start': order.start_datetime,
                'end': order.end_datetime,
            }
        dialogue_dict = {
            'dialogue_id': dialogue.id,
            'guest': guest_dict,
            'product': product_dict,
            'order': order_dict,
        }
        date_updated = datetime.date(dialogue.date_updated.year, dialogue.date_updated.month, dialogue.date_updated.day)
        if date_updated == today:
            today_list.append(dialogue_dict)
        elif date_updated == yesterday:
            yesterday_list.append(dialogue_dict)
        else:
            past_list.append(dialogue_dict)

    result = {
        'Today': today_list,
        'Yesterday': yesterday_list,
        'Past': past_list,
    }
    return CoastalJsonResponse(result)