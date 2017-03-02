from dateutil.rrule import rrule, DAILY
from itertools import chain
import logging

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm, FacebookLoginForm
from coastal.apps.account.utils import create_user
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import ValidateEmail, FavoriteItem
from coastal.apps.payment.stripe import get_stripe_info
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.account.models import UserProfile, CoastalBucket, InviteCode
from coastal.apps.sale.models import SaleOffer
from coastal.api.product.utils import bind_product_image, get_products_by_id, get_email_cipher
from coastal.apps.sns.utils import bind_token, unbind_token
from django.urls import reverse
from coastal.apps.product import defines as product_defs

logger = logging.getLogger(__name__)


def register(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    register_form = RegistrationForm(request.POST)
    if not register_form.is_valid():
        return CoastalJsonResponse(register_form.errors, status=response.STATUS_400)

    cleaned_data = register_form.cleaned_data
    user = create_user(cleaned_data['email'], cleaned_data['password'])
    logger.debug('Logging user is %s, User token is %s, User uuid is %s' %
                 (cleaned_data['email'], cleaned_data['token'], cleaned_data['uuid'], ))

    auth_login(request, user)
    if cleaned_data['uuid'] and cleaned_data['token']:
        bind_token(cleaned_data['uuid'], cleaned_data['token'], user)

    data = {
        'user_id': user.id,
        'logged': request.user.is_authenticated(),
        "has_agency_info": user.userprofile.has_agency_info,
        'email': user.email,
        'email_confirmed': user.userprofile.email_confirmed,
        'name': user.get_full_name(),
        'photo': user.basic_info()['photo'],
    }
    return CoastalJsonResponse(data)


def facebook_login(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = FacebookLoginForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    logger.debug('Logging user is %s, User token is %s, User uuid is %s, User name is %s, User client is Facebook' %
                 (form.cleaned_data['userid'], form.cleaned_data['token'], form.cleaned_data['uuid'], form.cleaned_data['name']))
    user = User.objects.filter(username=form.cleaned_data['userid']).first()
    if user:
        is_first = not bool(user.last_login)
        auth_login(request, user)
    else:
        name_list = form.cleaned_data['name'].split()
        user = User.objects.create(username=form.cleaned_data['userid'], email=form.cleaned_data['email'],
                                   first_name=name_list.pop(), last_name=' '.join(name_list))
        UserProfile.objects.create(user=user, email_confirmed='confirmed', client='facebook')
        CoastalBucket.objects.create(user=user)
        is_first = not bool(user.last_login)
        auth_login(request, user)

    if form.cleaned_data['token']:
        bind_token(form.cleaned_data['uuid'], form.cleaned_data['token'], user)

    data = {
        'user_id': user.id,
        'logged': user.is_authenticated(),
        "has_agency_info": user.userprofile.has_agency_info,
        'email': user.email,
        'email_confirmed': user.userprofile.email_confirmed,
        'name': user.get_full_name(),
        'photo': user.basic_info()['photo'],
        'first_login': is_first,
    }

    return CoastalJsonResponse(data)


def login(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
    logger.debug('Logging user is %s, User token is %s, User uuid is %s' %
                 (request.POST.get('username'), request.POST.get('token'), request.POST.get('uuid')))
    if user:
        is_first = not bool(user.last_login)
        auth_login(request, user)

        uuid = request.POST.get('uuid')
        token = request.POST.get('token')
        if uuid and token:
            bind_token(uuid, token, user)

        data = {
            'user_id': user.id,
            'logged': request.user.is_authenticated(),
            'has_agency_info': user.userprofile.has_agency_info,
            'email': user.email,
            'email_confirmed': user.userprofile.email_confirmed,
            'name': user.get_full_name(),
            'photo': user.basic_info()['photo'],
            'first_login': is_first,
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
            'exists': User.objects.filter(username=form.cleaned_data['email'].lower()).exists()
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
                if len(name_list) > 1:
                    setattr(user, 'last_name', name_list.pop())
                setattr(user, 'first_name', ' '.join(name_list))
            else:
                if key in form.cleaned_data:
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
            'photo': user.basic_info()['photo'],
            'purpose': user.userprofile.purpose,
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
        'photo': user.basic_info()['photo'],
        'purpose': user.userprofile.purpose
    }
    return CoastalJsonResponse(data)


def logout(request):
    if request.user.is_authenticated():
        logger.debug('Logout user is %s, unbind token is %s ' % (request.user, request.POST.get('token')))
        unbind_token(request.POST.get('token'), request.user)
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
    subject = 'Email Verification'
    message = '''Hi %s,

  To complete the process of publishing and transaction on Coastal, you must confirm your email address below:
http://%s/account/confirm-email/?token=%s
The link will be invalid 24 hours later. Please resend if this happens.

Thanks,
The Coastal Team
''' % (user.email, settings.SITE_DOMAIN, validate_instance.token)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], connection=None, html_message=None)
    data = {'email_confirmed': user.userprofile.email_confirmed}
    return CoastalJsonResponse(data)


@login_required
def my_activity(request):
    if request.method != 'GET':
        return CoastalJsonResponse(status=response.STATUS_405)

    result = {
        'recently_views': [],
        'orders': []
    }
    user = request.user
    recently_viewed = user.recently_viewed.order_by('-date_created')[0:20]
    products = get_products_by_id(recently_viewed.values_list('product_id', flat=True))
    for item in recently_viewed:
        p = products[item.product_id]
        result['recently_views'].append({
            'id': p.id,
            'name': p.name,
            'image': p.main_image and p.main_image.image.url or '',
            'status': p.status,
        })

    # now = datetime.now()
    yesterday = timezone.datetime.now() - timezone.timedelta(hours=24)
    active_orders = RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).exclude(
        status__in=RentalOrder.END_STATUS_LIST)
    finished_orders = RentalOrder.objects.filter(Q(owner=user) | Q(guest=user)).filter(
        status__in=RentalOrder.END_STATUS_LIST, date_updated__gt=yesterday)
    active_offers = SaleOffer.objects.filter(Q(owner=user) | Q(guest=user)).exclude(
        status__in=SaleOffer.END_STATUS_LIST)
    finished_offers = SaleOffer.objects.filter(Q(owner=user) | Q(guest=user)).filter(
        status__in=SaleOffer.END_STATUS_LIST, date_updated__gt=yesterday)

    orders = sorted(chain(active_orders, finished_orders, active_offers, finished_offers),
                    key=lambda instance: instance.date_updated,
                    reverse=True)

    for order in orders:
        if isinstance(order, RentalOrder):
            start_time = order.start_datetime
            end_time = order.end_datetime
            if order.product.category.get_root().id == product_defs.CATEGORY_ADVENTURE:
                date_format = '%A, %B, %d, %l:%M %p'
                if order.product.exp_time_unit == 'hour':
                    start_time_display = timezone.localtime(start_time, timezone.get_current_timezone()).strftime(date_format)
                    end_time_display = timezone.localtime(end_time, timezone.get_current_timezone()).strftime(date_format)
                else:
                    start_hour = order.product.exp_start_time.hour
                    end_hour = order.product.exp_end_time.hour
                    start_time_display = timezone.localtime(start_time, timezone.get_current_timezone()).replace(hour=start_hour).strftime(date_format)
                    end_time_display = timezone.localtime(end_time, timezone.get_current_timezone()).replace(hour=end_hour,minute=0).strftime(date_format)
            else:
                if order.rental_unit == 'day':
                    date_format = '%A, %B, %d'
                else:
                    date_format = '%A, %B, %d, %l:%M %p'
                start_time_display = timezone.localtime(start_time, timezone.get_current_timezone()).strftime(date_format)
                end_time_display = timezone.localtime(end_time, timezone.get_current_timezone()).strftime(date_format)

            guest_count_display = order.guest_count and ('%s people' % order.guest_count) or ''

            data = {
                'id': order.id,
                'owner': order.owner.basic_info(),
                'guest': order.guest.basic_info(),
                'product': {
                    'id': order.product_id,
                    'image': order.product.get_main_image(),
                    'name': order.product.name,
                },
                'start_date': start_time_display,
                'end_date': end_time_display,
                'total_price_display': order.get_total_price_display(),
                'status': order.get_status_display(),
                'type': 'rental'
            }
            if order.product.category.get_root().id != product_defs.CATEGORY_ADVENTURE:
                data['more_info'] = '%s %s' % (guest_count_display, order.get_time_length_display())
            if order.product.category.get_root().id == product_defs.CATEGORY_ADVENTURE:
                data['more_info'] = '%s' % guest_count_display
        else:
            data = {
                'id': order.id,
                'owner': order.owner.basic_info(),
                'guest': order.guest.basic_info(),
                'product': {
                    'id': order.product_id,
                    'image': order.product.get_main_image(),
                    'name': order.product.name,
                },
                'total_price_display': order.get_price_display(),
                'status': order.get_status_display(),
                'type': 'sale',
            }

        result['orders'].append(data)
    return CoastalJsonResponse(result)


@login_required
def my_account(request):
    user = request.user

    data = {
        'coastal_dollar': '$%s' % format(int(user.coastalbucket.balance), ','),
        'profile': {
            'name': user.get_full_name(),
            'email': user.email,
            'email_confirmed': user.userprofile.email_confirmed,
            'photo': user.basic_info()['photo'],
            'purpose': user.userprofile.purpose,
        }
    }

    # my products
    product_group = []
    product_list = user.properties.all()
    bind_product_image(product_list)
    for product in product_list:
        data_product = {
            'id': product.id,
            'name': product.name,
            'image': product.images[0].image.url if len(product.images) else '',
            # 'address': product.country + ',' + product.city,
            'address': product.address,
            'status': product.status,
            'type': product.get_product_type(),
        }

        product_group.append(data_product)
    data['my_products'] = product_group

    # my favorite
    favorite_group = []
    favorite_item = FavoriteItem.objects.filter(favorite__user=user)
    product_favorite = Product.objects.filter(favoriteitem__in=favorite_item)
    bind_product_image(product_favorite)
    for product in product_favorite:
        data_favorite = {
            'id': product.id,
            'name': product.name,
            'image': product.images[0].image.url if len(product.images) else '',
            'address': product.country + ',' + product.city,
            'type': product.get_product_type(),
            'status': product.status,
        }
        favorite_group.append(data_favorite)
    data['favorites'] = favorite_group

    # my orders
    yesterday = timezone.datetime.now() - timezone.timedelta(hours=24)
    rental_order_list = list(RentalOrder.objects.filter(
        Q(owner=user) | Q(guest=user), status__in=RentalOrder.END_STATUS_LIST, date_updated__lte=yesterday))
    sale_offer_list = list(SaleOffer.objects.filter(
        Q(owner=user) | Q(guest=user), status__in=SaleOffer.END_STATUS_LIST, date_updated__lte=yesterday))
    orders = sorted(chain(rental_order_list + sale_offer_list),
                    key=lambda instance: instance.date_updated,
                    reverse=True)

    data['orders'] = []
    for order in orders:
        order_info = {
            'id': order.id,
            'type': 'rental' if isinstance(order, RentalOrder) else 'sale',
            'image': order.product.get_main_image(),
            'owner_id': order.owner_id,
            'guest_id': order.guest_id,
        }

        if isinstance(order, RentalOrder):
            order_info['type'] = 'rental'

            if order.owner == request.user:
                order_info['name'] = '%s booked %s at your %s at %s' % (
                    order.guest.basic_info()['name'],
                    order.get_time_length_display(),
                    order.product.category.name,
                    order.product.city
                )
            else:
                order_info['name'] = 'I booked %s at %s\'s %s at %s' % (
                    order.get_time_length_display(),
                    order.owner.basic_info()['name'],
                    order.product.category.name,
                    order.product.city
                )
        else:
            order_info['type'] = 'sale'

            if request.user == order.owner:
                order_info['name'] = '%s bought %s at %s' % (
                    order.guest.basic_info()['name'],
                    order.product.category.name,
                    order.product.city)
            else:
                order_info['name'] = 'I bought %s\'s %s at %s' % (
                    order.owner.basic_info()['name'],
                    order.product.category.name,
                    order.product.city
                )

        data['orders'].append(order_info)
    return CoastalJsonResponse(data)


@login_required
def my_calendar(request):
    user = request.user

    month = timezone.datetime.strptime(request.GET.get('month'), '%Y-%m')
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
                    data = {
                        'date': begin_time.strftime('%Y-%m-%d'),
                        'date_display': begin_time.strftime('%B %d, %Y'),
                        'orders': order_result
                    }

                    data_result.append(data)
                orders[str(begin_time.day)] = order_result
            begin_time = begin_time + timezone.timedelta(days=1)

    return CoastalJsonResponse(data_result)


@login_required
def my_order_dates(request):
    user = request.user
    now_year = timezone.now()
    now_year = timezone.datetime(now_year.year, now_year.month, 1, tzinfo=now_year.tzinfo)
    next_year = timezone.datetime(now_year.year + 1, now_year.month, 1, tzinfo=now_year.tzinfo)
    order_list = user.owner_orders.filter(Q(end_datetime__gte=now_year) & Q(start_datetime__lt=next_year))
    date_list = []
    for order in order_list:
        begin_time, end_time = order.start_datetime, order.end_datetime
        for every_day in rrule(DAILY, dtstart=begin_time, until=end_time):
            if every_day >= now_year and every_day < next_year:
                format_day = timezone.datetime(every_day.year, every_day.month, every_day.day).strftime("%Y-%m-%d")
                if format_day not in date_list:
                    date_list.append(format_day)

    return CoastalJsonResponse(date_list)


@login_required
def my_orders(request):
    if not request.GET.get('date'):
        return CoastalJsonResponse({'date': 'The field is required.'}, status=response.STATUS_400)

    date = timezone.datetime.strptime(request.GET.get('date'), '%Y-%m-%d')
    start_time = timezone.make_aware(date)
    end_time = timezone.make_aware(date + timezone.timedelta(days=1))
    order_list = request.user.owner_orders.filter(Q(end_datetime__gte=start_time) & Q(start_datetime__lt=end_time))
    data = {
        'date': date.strftime('%Y-%m-%d'),
        'date_display': date.strftime('%B %d, %Y'),
        'orders': [],
    }
    for order in order_list:
        data['orders'].append({
            'id': order.id,
            'guests': order.guest_count,
            'product_name': order.product.name,
        })
    return CoastalJsonResponse(data)


@login_required
def stripe_info(request):
    return CoastalJsonResponse(get_stripe_info(request.user))


@login_required
def invite_codes(request):
    if not request.user.userprofile.invite_code:
        invite_code = InviteCode.objects.filter(used=False)[0].invite_code
        UserProfile.objects.filter(user=request.user).update(invite_code=invite_code)
        InviteCode.objects.filter(invite_code=invite_code).update(used=True)
    else:
        invite_code = request.user.userprofile.invite_code
    data = {
        'invite_code': invite_code,
        'invite_url': 'http://%s%s' % (settings.SITE_DOMAIN, reverse('account:sign-up', args=(invite_code,))),
        'invite_msg': '%s %s' % (request.user.first_name or 'Your friend', "invited you to join itsCoastal."),
        'award_msg': 'Sign up and get $35 off your first adventure.',
        'logo_url': 'http://%s%s' % (settings.SITE_DOMAIN, '/static/img/coastal.ico'),
    }

    return CoastalJsonResponse(data)
