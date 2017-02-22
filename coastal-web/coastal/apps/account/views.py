from django.http.response import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from coastal.apps.account.models import ValidateEmail, InviteRecord
from coastal.apps.account.utils import create_user
from coastal.apps.account.models import UserProfile
from django.contrib.auth.models import User
from coastal.api.account.forms import RegistrationForm
from django.template.response import TemplateResponse


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
    try:
        referrer = UserProfile.objects.get(invite_code=invite_code).user
    except UserProfile.DoesNotExist:
        referrer = None
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            user = create_user(cleaned_data['email'], cleaned_data['password'])
            if referrer:
                InviteRecord.objects.create(invite_code=invite_code, user=user, referrer=referrer)
                referrer.coastalbucket.balance += 10
                referrer.coastalbucket.save()
                user.coastalbucket.balance += 35
                user.coastalbucket.save()

            return TemplateResponse(request, 'successful.html')
    else:
        form = RegistrationForm()

    return TemplateResponse(request, 'sign-up.html', {'form': form, 'referrer': referrer})
