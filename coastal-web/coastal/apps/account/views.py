from django.http.response import HttpResponseRedirect
from django.utils import timezone
from coastal.apps.account.models import ValidateEmail, InviteRecord
from coastal.apps.account.utils import create_user
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.account.forms import RegistrationForm
from coastal.api.core import response
from coastal.apps.account.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from coastal.apps.sns.utils import bind_token


def validate_email_confirm(request):
    try:
        validate_email = ValidateEmail.objects.get(token=request.GET.get("token"))
    except ValidateEmail.DoesNotExist:
        return HttpResponseRedirect('/static/html/invalid-token.html')

    profile = validate_email.user.userprofile
    if profile.email_confirmed == 'confirmed':
        return HttpResponseRedirect('/static/html/confirm-email-success.html')

    if validate_email.expiration_date < timezone.now():
        return HttpResponseRedirect('/static/html/expired-token.html')

    profile.email_confirmed = 'confirmed'
    profile.save()
    return HttpResponseRedirect('/static/html/confirm-email-success.html')


def sign_up(request, invite_code):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    sign_up_form = RegistrationForm(request.POST)
    if not sign_up_form.is_valid():
        return CoastalJsonResponse(sign_up_form.errors, status=response.STATUS_400)

    cleaned_data = sign_up_form.cleaned_data
    user = create_user(cleaned_data['email'], cleaned_data['password'])
    auth_login(request, user)
    if cleaned_data['uuid'] and cleaned_data['token']:
        bind_token(cleaned_data['uuid'], cleaned_data['token'], user)
    referrer = User.objects.get(userprofile=UserProfile.objects.get(invite_code=invite_code))
    InviteRecord.objects.create(invite_code=invite_code, user=user, referrer=referrer)
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
