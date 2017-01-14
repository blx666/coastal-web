from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone
from django.db.models import Q
from dateutil.rrule import rrule, DAILY

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.apps.account.utils import create_user
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile, ValidateEmail, FavoriteItem
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.sale.models import SaleOffer
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
        timespan = timezone.now() - validate.created_date
        if timespan.total_seconds() < 300:
            data = {'email_confirmed': validate.user.userprofile.email_confirmed}
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
                The link will be invalid 24 hours later. Please resend if this happens.

                Thanks,
                The Coastal Team
                ''' % (user.email, settings.SITE_DOMAIN, validate_instance.token)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], connection=None, html_message=None)
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
    if request.method != 'GET':
        return CoastalJsonResponse(status=response.STATUS_405)
    order_list = []
    user = request.user
    now = datetime.now()
    start = now - timedelta(hours=23, minutes=59, seconds=59)
    orders_notfinished = list(RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).exclude(rental_unit__in=['finished', 'declined', 'invalid']))
    orders_finished = list(RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).filter(rental_unit__in=['finished', 'declined', 'invalid']).filter(date_created__gte=start))
    sale_offer_not_finished = list(SaleOffer.objects.filter(Q(owner=user) | Q(guest=user)).exclude(status__in=['finished', 'decline', 'invalid']))
    sale_offer_finished = list(SaleOffer.objects.filter(Q(owner=user) | Q(guest=user)).filter(status__in=['finished', 'decline', 'invalid']).filter(date_created__gte=start))

    if orders_finished and orders_notfinished:
        orders = orders_finished + orders_notfinished
    elif orders_finished and not orders_notfinished:
        orders = orders_finished
    elif not orders_finished and orders_notfinished:
        orders = orders_notfinished
    else:
        orders = []
    if orders:
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
                'total_price_display': order.get_total_price_display(),
                'more_info': more_info,
                'status': order.get_status_display(),
                'type': 'rental',
            }
            order_list.append(data)
    else:
        order_list = []

    if sale_offer_finished and sale_offer_not_finished:
        sale_offers = sale_offer_finished + sale_offer_not_finished
    elif sale_offer_finished and not sale_offer_not_finished:
        sale_offers = sale_offer_finished
    elif not sale_offer_finished and sale_offer_not_finished:
        sale_offers = sale_offer_not_finished
    else:
        sale_offers = []
    if sale_offers:
        for sale_offer in sale_offers:
            content = {
                'id': sale_offer.id,
                'owner': {
                    'id': sale_offer.owner_id,
                    'image': sale_offer.owner.userprofile.photo and sale_offer.owner.userprofile.photo.url or '',
                    'name': sale_offer.guest.get_full_name(),
                },
                'guest': {
                    'id': sale_offer.guest_id,
                    'image': sale_offer.guest.userprofile.photo and sale_offer.guest.userprofile.photo.url or '',
                    'name': sale_offer.guest.get_full_name(),
                },
                'product': {
                    'id': sale_offer.product_id,
                    'image': sale_offer.product.productimage_set.first() and sale_offer.product.productimage_set.first().image.url or '',
                    'name': sale_offer.product.name,
                },
                'price_display': sale_offer.get_price_display(),
                'status': sale_offer.get_status_display(),
                'type': 'sale',
            }
            order_list.append(content)

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
    order_rental_list = list(RentalOrder.objects.filter(Q(owner=user) | Q(guest=user),
                                                        status__in=['finished', 'declined', 'invalid'])
                             .order_by('date_created'))
    order_sale_list = list(SaleOffer.objects.filter(Q(owner=user) | Q(guest=user),
                                                    status__in=['finished', 'declined', 'invalid'])
                           .order_by('date_created'))
    order_list = order_rental_list + order_sale_list
    for order in order_list:
        if order.date_updated + timedelta(days=1) < timezone.now():
            data_order = {}
            data_order['id'] = order.id
            data_order['type'] = 'rental' if isinstance(order, RentalOrder) else 'sale'
            image = order.product.productimage_set.all()
            data_order['image'] = image[0].image.url if len(image) else ''
            data_order['title'] = order.number
            order_group.append(data_order)

    data['orders'] = order_group

    return CoastalJsonResponse(data)


@login_required
def my_calendar(request):
    user = request.user

    month = time.strptime(request.GET.get('month'), '%Y-%m')
    order_list = user.owner_orders.all()
    data_result = []
    orders = {}
    for order in order_list:
        begin_time, end_time = order.start_datetime, order.end_datetime
        order_result = []
        order_result.append({'id': order.id, 'guests': order.product.max_guests, 'product_name': order.product.name})
        while begin_time <= end_time:
            if (begin_time.year, begin_time.month) == (month.tm_year, month.tm_mon):
                if str(begin_time.day) in orders:
                    orders[str(begin_time.day)] = orders[str(begin_time.day)] + order_result
                    for update_order in data_result:
                        if begin_time.strftime('%Y-%m-%d') == update_order['date']:
                            update_order['orders'] = orders[str(begin_time.day)]
                            break
                else:
                    data = {}
                    data['date'] = begin_time.strftime('%Y-%m-%d')
                    data['date_display'] = begin_time.strftime('%B %d, %Y')
                    data['orders'] = order_result
                    data_result.append(data)
                orders[str(begin_time.day)] = order_result
            begin_time = begin_time + timedelta(days=1)

    return CoastalJsonResponse(data_result)


@login_required
def my_order_dates(request):
    user = request.user
    now_year = timezone.now()
    now_year = datetime(now_year.year, now_year.month, 1, tzinfo=now_year.tzinfo)
    next_year = datetime(now_year.year + 1, now_year.month, 1, tzinfo=now_year.tzinfo)
    order_list = user.owner_orders.filter(Q(end_datetime__gte=now_year) & Q(start_datetime__lt=next_year))
    date_list = []
    for order in order_list:
        begin_time, end_time = order.start_datetime, order.end_datetime
        for every_day in rrule(DAILY, dtstart=begin_time, until=end_time):
            if every_day >= now_year and every_day <  next_year:
                format_day = datetime(every_day.year, every_day.month, every_day.day).strftime("%Y-%m-%d")
                if format_day not in date_list:
                    date_list.append(format_day)

    return CoastalJsonResponse(date_list)


@login_required
def my_orders(request):
    user = request.user
    date = time.strptime(request.GET.get('date'), '%Y-%m-%d')
    date = datetime(date.tm_year, date.tm_mon, date.tm_mday, tzinfo=timezone.now().tzinfo)
    order_list = user.owner_orders.filter(Q(end_datetime__gte=date) & Q(start_datetime__lte=date))
    data = {}
    data['date'] = date.strftime('%Y-%m-%d')
    data['date_display'] = date.strftime('%B %d, %Y')
    orders = []
    for order in order_list:
        orders.append({'id': order.id, 'guests': order.product.max_guests, 'product_name': order.product.name})
    data['orders'] = orders
    return CoastalJsonResponse(data)


