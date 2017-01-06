from coastal.apps.message.models import Dialogue
from coastal.api.message.forms import DialogueForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.rental.models import RentalOrder
from django.contrib.gis.db.models import Q
from coastal.api.core.decorators import login_required
import datetime
from django.forms import model_to_dict
from coastal.apps.message.models import Message
from coastal.api.message.forms import MessageForm
from django.contrib.auth.models import User
from coastal.api import defines as defs
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger


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


@login_required
def send_message(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    message_form = MessageForm(request.POST)
    if not message_form.is_valid():
        return CoastalJsonResponse(message_form.errors, status=response.STATUS_400)

    receiver_id = message_form.cleaned_data['receiver']
    dialogue_id = message_form.cleaned_data['dialogue']
    content = message_form.cleaned_data['content']
    _type = message_form.cleaned_data['_type']

    sender_obj = request.user
    receiver_obj = User.objects.get(id=receiver_id)
    dialogue_obj = Dialogue.objects.get(id=dialogue_id)
    message = Message.objects.create(sender=sender_obj, receiver=receiver_obj, dialogue=dialogue_obj, content=content,
                                     _type=_type)

    result = {
        'message_id': message.id,
    }

    return CoastalJsonResponse(result)


@login_required
def dialogue_detail(request):
    dialogue_id = request.GET.get('dialogue_id')
    if not dialogue_id:
        return CoastalJsonResponse(status=response.STATUS_404)
    dialogue = Dialogue.objects.filter(id=dialogue_id).first()
    if not dialogue:
        return CoastalJsonResponse(status=response.STATUS_404)

    product_id = dialogue.product.id
    messages = Message.objects.filter(dialogue=dialogue)
    messages.update(read=True)
    page = request.GET.get('page', 1)
    item = defs.PER_PAGE_ITEM
    paginator = Paginator(messages, item)
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    if int(page) >= paginator.num_pages:
        next_page = 0
    else:
        next_page = int(page) + 1

    message_list = []
    for message in messages:
        message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', '_type', 'content'])
        message_dict['date_created'] = message.date_created.strftime('%m %d,%Y %H:%M %p')
        message_list.append(message_dict)

    result = {
        'next_page': next_page,
        'product_id': product_id,
        'messages': message_list,
    }

    return CoastalJsonResponse(result)


@login_required
def get_new_message(request):
    date_created = request.GET.get('date_created')
    dialogue_id = request.GET.get('dialogue_id')
    if not (date_created and dialogue_id):
        return CoastalJsonResponse(status=response.STATUS_404)
    date_created = datetime.datetime.strptime(date_created, '%Y%m%d%H%M%S')
    new_messages = Message.objects.filter(dialogue=dialogue_id, date_created__gt=date_created)
    new_messages.update(read=True)
    if not new_messages:
        return CoastalJsonResponse(status=response.STATUS_404)

    new_message_list = []
    for message in new_messages:
        message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', '_type', 'content'])
        message_dict['date_created'] = message.date_created.strftime('%m %d,%Y %H:%M %p')
        new_message_list.append(message_dict)

    result = {
        'new_messages': new_message_list,
    }

    return CoastalJsonResponse(result)