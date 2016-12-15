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
    data = {"has_agency_info": user.userprofile.has_agency_info, 'user_id': user.id}
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
            'user_id': user.id
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
    form = UserProfileForm(request.POST, instance=request.user.userprofile)
    if form.is_valid():
        form.save()
        return CoastalJsonResponse()
    return CoastalJsonResponse(form.errors, status=response.STATUS_400)





