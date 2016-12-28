from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile, ValidateEmail


def register(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    register_form = RegistrationForm(request.POST)
    if not register_form.is_valid():
        return CoastalJsonResponse(register_form.errors, status=response.STATUS_400)

    user = User.objects.create_user(username=register_form.cleaned_data['email'],
                                    email=register_form.cleaned_data['email'],
                                    password=register_form.cleaned_data['password'])
    UserProfile.objects.create(user=user)
    auth_login(request, user)
    data = {
        "has_agency_info": user.userprofile.has_agency_info,
        'user_id': user.id,
        'currency': 'USD',
        'name': user.get_full_name(),
        'email': user.email,
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
            'logged': request.user.is_authenticated(),
            'has_agency_info': user.userprofile.has_agency_info,
            'user_id': user.id,
            'currency': 'USD',
            'name': user.get_full_name(),
            'email': user.email,
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
            'name': user.get_full_name(),
            'email': user.email,
            'photo': user.userprofile.photo.url if user.userprofile.photo else '',
        }
        return CoastalJsonResponse(data)
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)


@login_required
def my_profile(request):
    user = request.user
    data = {
        'name': user.get_full_name(),
        'email': user.email,
        'photo': user.userprofile.photo.url if user.userprofile.photo else '',
        'is_agent': user.userprofile.is_agent,
        'agency_email': user.userprofile.agency_email,
        'agency_name': user.userprofile.agency_name,
        'agency_address': user.userprofile.agency_address,
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
    validate_instance = ValidateEmail()
    validate_list = user.validateemail_set.values('id')

    if len(validate_list) == 0:
        validate_instance.save(user=user)
        subject = 'user validate email'
        message = 'This is a validate email, please complete certification within 24 hours http://' + settings.SITE_DOMAIN \
                  + '/api/account/validate-email/confirm/?token=' + validate_instance.token
        send_mail(subject, message, settings.SUBSCRIBE_EMAIL, [user.email], connection=None, html_message=None)

        user.userprofile.email_confirmed = 'sending'
        user.userprofile.save()
        data = {'email_confirmed': user.userprofile.email_confirmed}
        return CoastalJsonResponse(data)

    validate_id = max([id_dict['id'] for id_dict in validate_list])
    exit_validate = ValidateEmail.objects.get(id=validate_id)
    timespan = timezone.now() - exit_validate.created_date

    if timespan.total_seconds() < 300:
        data = {'email_confirmed': exit_validate.user.userprofile.email_confirmed}
        return CoastalJsonResponse(data)
    validate_instance.save(user=user)
    subject = 'user validate email'
    message = 'This is a validate email, please complete certification within 24 hours http://' + settings.SITE_DOMAIN \
              + '/api/account/validate-email/confirm/?token=' + validate_instance.token
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
