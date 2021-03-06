from coastal.apps.message.models import Dialogue, Message
from coastal.api.message.forms import DialogueForm
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.sale.models import SaleOffer
from django.contrib.gis.db.models import Q
from coastal.api.core.decorators import login_required
import datetime
from django.forms import model_to_dict
from coastal.api.message.forms import MessageForm
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from coastal.apps.sns.utils import publish_message
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint


@login_required
def create_dialogue(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = DialogueForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    if form.cleaned_data['is_owner']:
        if request.POST.get('rental_order_id'):
            try:
                order = RentalOrder.objects.get(id=request.POST['rental_order_id'])
            except RentalOrder.DoesNotExist:
                return CoastalJsonResponse({'rental_order_id': 'The order does not exist.'},
                                           status=response.STATUS_400)
            owner, guest, product = order.owner, order.guest, order.product
        elif request.POST.get('sale_offer_id'):
            try:
                offer = SaleOffer.objects.get(id=request.POST['sale_offer_id'])
            except RentalOrder.DoesNotExist:
                return CoastalJsonResponse({'sale_offer_id': 'The sale offer does not exist.'},
                                           status=response.STATUS_400)
            owner, guest, product = offer.owner, offer.guest, offer.product
        else:
            return CoastalJsonResponse(status=response.STATUS_400)
    else:
        product_id = form.cleaned_data['product_id']
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return CoastalJsonResponse(status=response.STATUS_404)
        owner, guest = product.owner, request.user

    order = RentalOrder.objects.filter(owner=owner, guest=guest,
                                       product=product).last()
    dialogue, _ = Dialogue.objects.get_all_queryset().update_or_create(owner=owner, guest=guest,
                                                                       product=product, defaults={'order': order, 'is_deleted': False})
    result = {
        'dialogue_id': dialogue.id,
    }
    return CoastalJsonResponse(result)


@login_required
def dialogue_list(request):
    dialogues = Dialogue.objects.filter(Q(owner=request.user) | Q(guest=request.user)).order_by('-date_updated')
    dialogues = dialogues.annotate(num_all_messages=Count('message', distinct=True)).filter(num_all_messages__gt=0)
    unread_dialogues = dialogues.filter(message__receiver=request.user, message__read=False).annotate(num_messages=Count('message', distinct=True))
    unread_dialogue_count_dict = {dialogue.id: dialogue.num_messages for dialogue in unread_dialogues}
    dialogues = dialogues[:100]
    dialogues_list = []

    for dialogue in dialogues:
        contact = request.user == dialogue.owner and dialogue.guest or dialogue.owner
        product = dialogue.product
        order = dialogue.order
        unread_message_number = unread_dialogue_count_dict.get(dialogue.id, 0)
        contact_dict = {
            'user_id': contact.id,
            'name': contact.basic_info()['name'],
            'photo': contact.basic_info()['photo'],
        }
        product_dict = {
            'product_id': product.id,
            'name': product.name,
            'image': product.get_main_image(),
            'for_rental': product.for_rental,
            'for_sale': product.for_sale,
            'currency': product.currency,
        }
        order_dict = {}
        if order:
            order_dict = {
                'order_id': order.id,
                'status': order.get_status_display(),
                'start': order.start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'end': order.end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            }
        dialogue_dict = {
            'dialogue_id': dialogue.id,
            'contact': contact_dict,
            'product': product_dict,
            'order': order_dict,
            'unread': unread_message_number,
            'date_update': dialogue.date_updated.strftime('%Y-%m-%d %H:%M:%S')
        }
        dialogues_list.append(dialogue_dict)

    result = {
        'dialogues': dialogues_list,
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

    sender_obj = request.user
    receiver_obj = User.objects.filter(id=receiver_id).first()
    dialogue_obj = Dialogue.objects.filter(id=dialogue_id).first()
    if not (receiver_obj and dialogue_obj):
        return CoastalJsonResponse(message_form.errors, status=response.STATUS_400)

    message = Message.objects.create(sender=sender_obj, receiver=receiver_obj, dialogue=dialogue_obj, content=content)
    dialogue_obj.save()

    sender_name = sender_obj.first_name
    try:
        publish_message(content, dialogue_id, receiver_obj, sender_name)
    except (NoEndpoint, DisabledEndpoint):
        pass

    result = {
        'message_id': message.id,
        'date_created': message.date_created.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return CoastalJsonResponse(result)


@login_required
def dialogue_detail(request):
    dialogue_id = request.GET.get('dialogue_id')

    message_time = request.GET.get('message_time')
    direction = request.GET.get('direction')

    if not dialogue_id:
        return CoastalJsonResponse(status=response.STATUS_400)

    dialogue = Dialogue.objects.filter(id=dialogue_id).first()
    if not dialogue:
        return CoastalJsonResponse(status=response.STATUS_404)
    product_id = dialogue.product.id

    if not (message_time or direction):
        messages = Message.objects.filter(dialogue=dialogue).order_by('-date_created')

        for single_message in messages:
            if single_message.receiver == request.user:
                single_message.read = True
                single_message.save()

        messages = messages[:20]
        message_list = []
        for message in messages:
            message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', 'content'])
            message_dict['date_created'] = message.date_created.strftime('%Y-%m-%d %H:%M:%S')
            message_list.append(message_dict)
        message_list.reverse()

        result = {
            'product_id': product_id,
            'messages': message_list,
        }

    if (message_time or direction) and not (message_time and direction):
        return CoastalJsonResponse(status=response.STATUS_400)

    if message_time and direction:
        message_time = datetime.datetime.strptime(message_time, '%Y-%m-%d %H:%M:%S')
        message_time = timezone.make_aware(message_time, timezone.UTC())
        if direction == 'up':
            up_messages = Message.objects.filter(dialogue=dialogue, date_created__lt=message_time).order_by('-date_created')

            for single_message in up_messages:
                if single_message.receiver == request.user:
                    single_message.read = True
                    single_message.save()

            up_messages = up_messages[:20]
            up_message_list = []
            for message in up_messages:
                up_message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', 'content'])
                up_message_dict['date_created'] = message.date_created.strftime('%Y-%m-%d %H:%M:%S')
                up_message_list.append(up_message_dict)
            up_message_list.reverse()

            result = {
                'product_id': product_id,
                'messages': up_message_list,
            }

        if direction == 'down':
            down_messages = Message.objects.filter(dialogue=dialogue, date_created__gt=message_time).order_by('-date_created')

            for single_message in down_messages:
                if single_message.receiver == request.user:
                    single_message.read = True
                    single_message.save()

            down_message_list = []
            for message in down_messages:
                down_message_dict = model_to_dict(message, fields=['id', 'sender', 'receiver', 'content'])
                down_message_dict['date_created'] = message.date_created.strftime('%Y-%m-%d %H:%M:%S')
                down_message_list.append(down_message_dict)
            down_message_list.reverse()

            result = {
                'product_id': product_id,
                'messages': down_message_list[1:],
            }

    return CoastalJsonResponse(result)
