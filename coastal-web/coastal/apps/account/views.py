from django.http.response import HttpResponseRedirect
from django.utils import timezone
from coastal.apps.account.models import ValidateEmail


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
