from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.apps.account.utils import create_user
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile, ValidateEmail, FavoriteItem
from coastal.api.product.utils import bind_product_image
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.rental.models import RentalOrder


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
    validate_list = user.validateemail_set.values('id')

    if len(validate_list) != 0:
        validate_id = max([id_dict['id'] for id_dict in validate_list])
        exit_validate = ValidateEmail.objects.get(id=validate_id)
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
                The Coastal Team''' % (user.eamil, settings.SITE_DOMAIN, validate_instance.token)
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



