from coastal.apps.message.models import Dialogue
from coastal.api.message.forms import DialogueForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.rental.models import RentalOrder
from django.contrib.gis.db.models import Q
from coastal.api.core.decorators import login_required
import datetime
from django.db.models import Count


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
    dialogue, _ = Dialogue.objects.get_all_queryset().update_or_create(owner=product.owner, guest=request.user,
                                                                       product=product, order=order, defaults={'is_deleted': False})

    result = {
        'dialogue_id': dialogue.id,
    }
    return CoastalJsonResponse(result)


@login_required
def dialogue_list(request):
    dialogues = Dialogue.objects.filter(Q(owner=request.user) | Q(guest=request.user)).order_by('-date_updated')
    unread_dialogues = dialogues.filter(message__read=False).annotate(num_messages=Count('message'))
    unread_dialogue_count_dict = {dialogue.id: dialogue.num_messages for dialogue in unread_dialogues}
    dialogues = dialogues[:100]
    today = datetime.date.today()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    today_list = []
    yesterday_list = []
    past_list = []

    for dialogue in dialogues:
        contact = request.user == dialogue.owner and dialogue.guest or dialogue.owner
        product = dialogue.product
        order = dialogue.order
        unread_message_number = unread_dialogue_count_dict.get(dialogue.id, 0)
        contact_dict = {
            'user_id': contact.id,
            'name': contact.get_full_name(),
            'photo': contact.userprofile.photo.url if contact.userprofile.photo else '',
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
            'contact': contact_dict,
            'product': product_dict,
            'order': order_dict,
            'unread': unread_message_number,
        }
        date_updated = datetime.date(dialogue.date_updated.year, dialogue.date_updated.month, dialogue.date_updated.day)
        if date_updated == today:
            today_list.append(dialogue_dict)
        elif date_updated == yesterday:
            yesterday_list.append(dialogue_dict)
        else:
            past_list.append(dialogue_dict)

    result = {
        'today': today_list,
        'yesterday': yesterday_list,
        'past': past_list,
    }
    return CoastalJsonResponse(result)


@login_required
def delete_dialogue(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    dialogue = Dialogue.objects.filter(id=request.POST.get('dialogue_id')).first()
    if not dialogue:
        return CoastalJsonResponse(status=response.STATUS_404)

    dialogue.is_deleted = True
    dialogue.save()
    return CoastalJsonResponse()