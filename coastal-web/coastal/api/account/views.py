from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.api.core import response
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import UserProfile


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
    data = {"has_agency_info": user.userprofile.has_agency_info, 'user_id': user.id, 'currency': 'USD'}
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
            'currency': 'USD'
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
        return CoastalJsonResponse()
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)


@login_required
def my_profile(request):
    user = request.user
    data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'photo': user.userprofile.photo.url,
        'is_agent': user.userprofile.is_agent,
        'agency_email': user.userprofile.agency_email,
        'agency_name': user.userprofile.agency_name,
        'agency_address': user.agency_address.agency_address,
    }
    return CoastalJsonResponse(data)
