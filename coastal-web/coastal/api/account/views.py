from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from coastal.api.account.forms import RegistrationForm, UserProfileForm, CheckEmailForm
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE
from coastal.apps.account.models import UserProfile


def register(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)

    register_form = RegistrationForm(request.POST)
    if not register_form.is_valid():
        return CoastalJsonResponse(register_form.errors, status=400)

    user = User.objects.create_user(username=register_form.cleaned_data['email'],
                                    email=register_form.cleaned_data['email'],
                                    password=register_form.cleaned_data['password'])
    UserProfile.objects.create(user=user)
    data = {"has_agency_info": user.userprofile.has_agency_info}
    return CoastalJsonResponse(data)


def login(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)

    user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
    if user:
        auth_login(request, user)
        data = {
            'logged': request.user.is_authenticated(),
            'has_agency_info': user.userprofile.has_agency_info,
        }
    else:
        data = {
            "logged": request.user.is_authenticated(),
            "error": STATUS_CODE.get(1000),
        }
    return CoastalJsonResponse(data)


def check_email(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)

    form = CheckEmailForm(request.POST)
    if form.is_valid():
        return CoastalJsonResponse({
            'exists': User.objects.filter(email=form.cleaned_data['email']).exists()
        })
    return CoastalJsonResponse(message=form.errors, status=400)


@login_required
def update_profile(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)
    form = UserProfileForm(request.POST, instance=request.user.userprofile)
    if form.is_valid():
        form.save()
        return CoastalJsonResponse()
    return CoastalJsonResponse(form.errors, status=400)


