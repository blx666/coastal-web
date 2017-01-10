from coastal.apps.message.models import Dialogue, Message
from coastal.api.message.forms import DialogueForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.rental.models import RentalOrder
from django.contrib.gis.db.models import Q
from coastal.api.core.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from coastal.api import defines as defs
import datetime
from django.forms import model_to_dict
from coastal.api.message.forms import MessageForm
from django.contrib.auth.models import User
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
    dialogue, _ = Dialogue.objects.update_or_create(owner=product.owner, guest=request.user,
                                                    product=product, order=order)

    result = {
        'dialogue_id': dialogue.id,
    }
    return CoastalJsonResponse(result)


@login_required
def dialogue_list(request):
    dialogues = Dialogue.objects.filter(Q(owner=request.user) | Q(guest=request.user)).order_by('-date_updated')
    unread_dialogues = dialogues.filter(message__read=False).annotate(num_messages=Count('message'))
    unread_dialogue_count_dict = {dialogue.id: dialogue.num_messages for dialogue in unread_dialogues}

    today = datetime.date.today()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    today_list = []
    yesterday_list = []
    past_list = []

    page = request.GET.get('page', 1)
    item = defs.PER_PAGE_ITEM
    paginator = Paginator(dialogues, item)
    try:
        dialogues = paginator.page(page)
    except PageNotAnInteger:
        dialogues = paginator.page(1)
    except EmptyPage:
        dialogues = paginator.page(paginator.num_pages)

    if int(page) >= paginator.num_pages:
        next_page = 0
    else:
        next_page = int(page) + 1

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
        'next_page': next_page,
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

    message_time = request.GET.get('message_time')
    direction = request.GET.get('direction')

    if not dialogue_id:
        return CoastalJsonResponse(status=response.STATUS_404)
    dialogue = Dialogue.objects.filter(id=dialogue_id).first()
    if not dialogue:
        return CoastalJsonResponse(status=response.STATUS_404)
    product_id = dialogue.product.id

    if not (message_time or direction):
        messages = Message.objects.filter(dialogue=dialogue).order_by('-date_created')
        messages.update(read=True)
        messages = messages[:20]
        message_list = []
        for message in messages:
            message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', '_type', 'content'])
            message_dict['date_created'] = message.date_created.strftime("%Y%m%d%H%M%S")
            message_list.append(message_dict)
        message_list.reverse()

        result = {
            'product_id': product_id,
            'messages': message_list,
        }

    if message_time and direction:
        message_time = datetime.datetime.strptime(message_time, '%Y%m%d%H%M%S')
        if direction == 'up':
            messages = Message.objects.filter(dialogue=dialogue, date_created__lt=message_time).order_by('-date_created')
            messages.update(read=True)
            messages = messages[:20]
            message_list = []
            for message in messages:
                message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', '_type', 'content'])
                message_dict['date_created'] = message.date_created.strftime("%Y%m%d%H%M%S")
                message_list.append(message_dict)
            message_list.reverse()

            result = {
                'product_id': product_id,
                'messages': message_list,
            }

        if direction == 'down':
            messages = Message.objects.filter(dialogue=dialogue, date_created__gt=message_time).order_by('-date_created')
            messages.update(read=True)
            message_list = []
            for message in messages:
                message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', '_type', 'content'])
                message_dict['date_created'] = message.date_created
                message_dict['message_time'] = message_time
                message_list.append(message_dict)
            message_list.reverse()

            result = {
                'product_id': product_id,
                'messages': message_list,
            }

    return CoastalJsonResponse(result)
