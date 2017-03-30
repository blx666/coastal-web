from coastal.api.core.response import CoastalJsonResponse
from django.utils import timezone
from coastal.apps.account.models import ValidateEmail, InviteRecord
from coastal.apps.account.utils import create_user, reward_invite_user
from coastal.apps.account.models import UserProfile
from coastal.api.account.forms import RegistrationForm
from django.template.response import TemplateResponse
from coastal.apps.account.form import PassWordResetFromEmail, SetPasswordForm

from django.conf import settings
from django.contrib.auth import get_user_model


from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext as _


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

    reward_invite_user(profile.user)

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

            return TemplateResponse(request, 'successful.html')
    else:
        form = RegistrationForm()

    return TemplateResponse(request, 'sign-up.html', {'form': form, 'referrer': referrer})


def password_reset(request,
                   email_template_name='registration/password_reset_email.html',
                   password_reset_form=PassWordResetFromEmail,
                   from_email=settings.DEFAULT_FROM_EMAIL,
                   extra_context=None,
                   html_email_template_name=None,
                   extra_email_context=None):
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': 'Reset Your Password',
                'request': request,
                'html_email_template_name': html_email_template_name,
                'extra_email_context': extra_email_context,
            }
            form.save(**opts)
            email = form.cleaned_data['email']
            active_users = get_user_model()._default_manager.filter(
                email__iexact=email, is_active=True)
            if active_users:
                return CoastalJsonResponse(data={'send_email': 'true'})
    else:
        form = password_reset_form()
    context = {
        'form': form,
        'title': _('Password reset'),
    }
    if extra_context is not None:
        context.update(extra_context)

    return CoastalJsonResponse(data={'send_email': 'false'})


def password_reset_done(request,
                        template_name='registration/password_reset_done.html',
                        extra_context=None):
    context = {
        'title': _('Password reset sent'),
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)


def password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('account:password_reset_complete')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        title = _('Enter new password')
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(user)
    else:
        validlink = False
        form = None
        title = _('Password reset unsuccessful')
    context = {
        'form': form,
        'title': title,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)


def password_reset_complete(request,
                            template_name='registration/password_reset_complete.html',
                            extra_context=None):
    context = {
        'login_url': resolve_url(settings.LOGIN_URL),
        'title': _('Password reset complete'),
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)
