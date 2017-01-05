from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone
from django.db.models import Q

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.apps.account.utils import create_user
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile, ValidateEmail
from coastal.apps.rental.models import RentalOrder
from coastal.api.product.utils import get_price_display
from datetime import datetime, timedelta, time
from coastal.apps.product import defines as defs
from coastal.api.product.utils import bind_product_image
import time
import math


def register(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    register_form = RegistrationForm(request.POST)
    if not register_form.is_valid():
        return CoastalJsonResponse(register_form.errors, status=response.STATUS_400)

    user = create_user(register_form.cleaned_data['email'], register_form.cleaned_data['password'])
    auth_login(request, user)
    data = {
        'user_id': user.id,
        'logged': request.user.is_authenticated(),
        "has_agency_info": user.userprofile.has_agency_info,
        'email': user.email,
        'email_confirmed': user.userprofile.email_confirmed,
        'name': user.get_full_name(),
        'photo': user.userprofile.photo.url if user.userprofile.photo else '',
    }
    return CoastalJsonResponse(data)


def login(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
    if user:
        auth_login(request, user)
        data = {
            'user_id': user.id,
            'logged': request.user.is_authenticated(),
            'has_agency_info': user.userprofile.has_agency_info,
            'email': user.email,
            'email_confirmed': user.userprofile.email_confirmed,
            'name': user.get_full_name(),
            'photo': user.userprofile.photo.url if user.userprofile.photo else '',
        }
    else:
        data = {
            "logged": request.user.is_authenticated(),
            "error": 'The username and password are not matched.',
        }
    return CoastalJsonResponse(data)


def check_email(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = CheckEmailForm(request.POST)
    if form.is_valid():
        return CoastalJsonResponse({
            'exists': User.objects.filter(email=form.cleaned_data['email']).exists()
        })
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)


@login_required
def update_profile(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = UserProfileForm(request.POST, request.FILES)
    if form.is_valid():
        user = request.user
        if request.FILES:
            setattr(user.userprofile, 'photo', form.cleaned_data['photo'])
        for key in form.data:
            if key == 'name':
                name_list = form.cleaned_data['name'].split()
                setattr(user, 'first_name', name_list.pop())
                setattr(user, 'last_name', ' '.join(name_list))
            else:
                setattr(user.userprofile, key, form.cleaned_data[key])
        user.save()
        user.userprofile.save()
        data = {
            'user_id': user.id,
            'logged': request.user.is_authenticated(),
            'has_agency_info': user.userprofile.has_agency_info,
            'email': user.email,
            'email_confirmed': user.userprofile.email_confirmed,
            'name': user.get_full_name(),
            'photo': user.userprofile.photo.url if user.userprofile.photo else '',
        }
        return CoastalJsonResponse(data)
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)


@login_required
def my_profile(request):
    user = request.user
    data = {
        'user_id': user.id,
        'logged': request.user.is_authenticated(),
        'has_agency_info': user.userprofile.has_agency_info,
        'email': user.email,
        'email_confirmed': user.userprofile.email_confirmed,
        'name': user.get_full_name(),
        'photo': user.userprofile.photo.url if user.userprofile.photo else '',
    }
    return CoastalJsonResponse(data)


@login_required
def logout(request):
    auth_logout(request)
    return CoastalJsonResponse()


@login_required
def validate_email(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    user = request.user
    validate = user.validateemail_set.order_by('created_date').first()
    if validate:
        exit_validate = ValidateEmail.objects.get(id=validate.id)
        timespan = timezone.now() - exit_validate.created_date
        if timespan.total_seconds() < 300:
            data = {'email_confirmed': exit_validate.user.userprofile.email_confirmed}
            return CoastalJsonResponse(data)
    else:
        user.userprofile.email_confirmed = 'sending'
        user.userprofile.save()
    validate_instance = ValidateEmail()
    validate_instance.save(user=user)
    subject = 'user validate email'
    message = '''Hi %s,

                To complete the process of publishing and transaction on Coastal, you must confirm your email address below:
                http://%s/api/account/validate-email/confirm/?token=%s
                The link will be valid 24 hours later. Please resend if this happens.

                Thanks,
                The Coastal Team
                ''' % (user.email, settings.SITE_DOMAIN, validate_instance.token)
    send_mail(subject, message, settings.SUBSCRIBE_EMAIL, [user.email], connection=None, html_message=None)
    data = {'email_confirmed': user.userprofile.email_confirmed}
    return CoastalJsonResponse(data)


def validate_email_confirm(request):
    try:
        validate_email = ValidateEmail.objects.get(token=request.GET.get("token"))

        userprofile = validate_email.user.userprofile
        if userprofile.email_confirmed == 'confirmed':
            return HttpResponse('user already  validate')

        if validate_email.expiration_date >= timezone.now():
            # not expiration date
            userprofile.email_confirmed = 'confirmed'
            userprofile.save()
            return CoastalJsonResponse()
        return HttpResponse('token already  expire')
    except validate_email.DoesNotExist:
        return HttpResponse('token is not exist')


@login_required
def my_activity(request):
    user = request.user
    now = datetime.now()
    start = now - timedelta(hours=23, minutes=59, seconds=59)
    orders_notfinished = list(RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).exclude(rental_unit__in=['finished', 'declined']))
    orders_finished = list(RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).filter(rental_unit__in=['finished', 'declined']).filter(date_created__gte=start))
    if orders_finished and orders_notfinished:
        orders = orders_finished + orders_notfinished
    elif orders_finished and not orders_notfinished:
        orders = orders_finished
    elif not orders_finished and orders_notfinished:
        orders = orders_notfinished
    else:
        orders = []
    if orders:
        order_list = []
        for order in orders:
            start_time = order.start_datetime
            end_time = order.end_datetime
            if order.product.rental_unit == 'day':
                start_datetime = datetime.strftime(start_time, '%A, %B %dst')
                end_datetime = datetime.strftime(end_time, '%A, %B %dst')
            else:
                start_datetime = datetime.strftime(start_time, '%A, %B %dst %H')
                end_datetime = datetime.strftime(end_time, '%A, %B %dst %H')
            if order.product.rental_unit == 'day':
                if order.product.category_id in (defs.CATEGORY_BOAT_SLIP, defs.CATEGORY_YACHT):
                    time_info = math.ceil((time.mktime(end_time.timetuple())-time.mktime(start_time.timetuple()))/(3600*24))+1
                else:
                    time_info = math.ceil((time.mktime(end_time.timetuple()) - time.mktime(start_time.timetuple()))/(3600*24))
            if order.product.rental_unit == 'half-day':
                time_info = math.ceil((time.mktime(end_time.timetuple())-time.mktime(start_time.timetuple()))/(3600*6))
            if order.product.rental_unit == 'hour':
                time_info = math.ceil((time.mktime(end_time.timetuple())-time.mktime(start_time.timetuple()))/3600)
            if time_info > 1:
                more_info = '%s people %s %ss' % (order.guest_count, time_info, order.product.rental_unit.title())
            else:
                more_info = '%s people %s %s' % (order.guest_count, time_info, order.product.rental_unit.title())
            data = {
                'id': order.id,
                'owner': {
                    'id': order.owner_id,
                    'photo': order.owner.userprofile.photo and order.owner.userprofile.photo.url or '',
                    'name': order.owner.get_full_name(),
                },
                'guest': {
                    'id': order.guest_id,
                    'photo': order.guest.userprofile.photo and order.guest.userprofile.photo.url or '',
                    'name': order.guest.get_full_name(),
                },
                'product': {
                    'id': order.product_id,
                    'image': order.product.productimage_set.first() and order.product.productimage_set.first().image.url or '',
                    'name': order.product.name,
                },
                'start_date': start_datetime,
                'end_date': end_datetime,
                'total_price_display': get_price_display(order.product, order.total_price),
                'more_info': more_info,
                'status': order.status,
            }
            order_list.append(data)
    else:
        order_list = []

    if user.recently_viewed.all():
        recently_views = user.recently_viewed.all()[0:20]
        recently_view_list = []
        for recently_view in recently_views:
            data = {
                'id': recently_view.product.id,
                'name': recently_view.product.name,
                'image': recently_view.product.productimage_set.first() and recently_view.product.productimage_set.first().image.url or ''
            }
            recently_view_list.append(data)
        result = {
            'recently_views': recently_view_list,
            'order': order_list,
        }
    else:
        result = {
            'order': order_list,
        }
    return CoastalJsonResponse(result)


@login_required
def my_account(request):
    user = request.user

    data = {}
    data['coastal_dollar'] = user.coastalbucket.balance if hasattr(user, 'coastalbucket') else 0

    # userprofile
    data['profile'] = {
        'name': user.get_full_name(),
        'email': user.email,
        'email_confirmed': user.userprofile.email_confirmed,
        'photo': user.userprofile.photo.url if user.userprofile.photo else '',
    }

    # my products
    product_group = []
    product_list = user.properties.all()
    bind_product_image(product_list)
    for product in product_list:
        data_product = {}
        data_product['id'] = product.id
        data_product['name'] = product.name
        data_product['image'] = product.images[0].image.url if len(product.images) else ''
        data_product['address'] = product.country + ',' + product.city
        data_product['status'] = product.status
        product_group.append(data_product)
    data['my_products'] = product_group

    # my favorite
    favorite_group = []
    favorite_item = FavoriteItem.objects.filter(favorite__user=user)
    product_favorite = Product.objects.filter(favoriteitem__in=favorite_item)
    bind_product_image(product_favorite)
    for product in product_favorite:
        data_favorite = {}
        data_favorite['id'] = product.id
        data_favorite['name'] = product.name
        data_favorite['image'] = product.images[0].image.url if len(product.images) else ''
        data_favorite['address'] = product.country + ',' + product.city
        favorite_group.append(data_favorite)
    data['favorites'] = favorite_group

    # my orders
    order_group = []
    order_list = user.owner_orders.all()
    for order in order_list:
        data_order = {}
        data_order['id'] = order.id
        data_order['type'] = order.rental_unit
        image = order.product.productimage_set.all()
        data_order['image'] = image[0].image.url if len(image) else ''
        data_order['title'] = order.number
        order_group.append(data_order)
    data['orders'] = order_group

    return CoastalJsonResponse(data)



