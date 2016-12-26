from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http.response import HttpResponse

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile, ValidateEmail
from datetime import datetime, timedelta


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
        'first_name': user.first_name,
        'last_name': user.last_name,
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
            'first_name': user.first_name,
            'last_name': user.last_name,
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
            if key in ('first_name', 'last_name'):
                setattr(user, key, form.cleaned_data[key])
            else:
                setattr(user.userprofile, key, form.cleaned_data[key])
        user.save()
        user.userprofile.save()
        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'photo': user.userprofile.photo.url if user.userprofile.photo else '',
        }
        return CoastalJsonResponse(data)
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)


@login_required
def my_profile(request):
    user = request.user
    data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
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
    validate_instance.save(user=user)
    subject = 'user validate email'
    message = 'This is a validate email, please complete certification within 24 hours http://'+settings.SITE_DOMAIN+'/api' \
              '/account/validate-email/confirm/?token=' + validate_instance.token
    send_mail(subject, message, settings.SUBSCRIBE_EMAIL, [user.email], connection=None, html_message=None)
    return CoastalJsonResponse()


def validate_email_confirm(request):
    validate_email_list = ValidateEmail.objects.filter(token=request.GET.get("token"))
    if not validate_email_list:
        # token is null
        return HttpResponse('token is not exist')
    for validate in validate_email_list:
        time_span = validate.expiration_date.replace(tzinfo=None) - datetime.now()
        user = validate.user.userprofile
        if user.email_confirmed:
            return HttpResponse('user already  validate')
        if time_span.days >= 0:
            # not expiration date
            user.email_confirmed = True
            user.save()
            return CoastalJsonResponse()
    return HttpResponse('token already  expire')


