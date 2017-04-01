from django import forms
from django.contrib.auth.models import User
from coastal.apps.account.models import UserProfile
from django.core.mail import EmailMessage
from django.template import loader
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from coastal import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(error_messages={'invalid': 'Please enter a valid email address'})
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, error_messages={'min_length': 'Password should be at least 6 characters.'})
    uuid = forms.CharField(required=False)
    token = forms.CharField(required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email.lower()).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    class Meta:
        model = User
        fields = ['email', 'password']


class UserProfileForm(forms.ModelForm):
    name = forms.CharField(max_length=128, required=False)
    is_agent = forms.CharField(required=False)

    def clean_is_agent(self):
        # TODO: is_agent is not required
        value = self.cleaned_data['is_agent']
        if value:
            if value not in ('0', '1'):
                raise forms.ValidationError("The value should be boolean: 0/1")
            return value == '1'

    class Meta:
        model = UserProfile
        fields = ['agency_email', 'agency_name', 'agency_address', 'photo', 'purpose']


class CheckEmailForm(forms.Form):
    email = forms.EmailField(required=True)


class FacebookLoginForm(forms.Form):
    userid = forms.CharField()
    email = forms.EmailField()
    name = forms.CharField(max_length=128)
    token = forms.CharField(required=False)
    uuid = forms.CharField(required=False)

    def clean(self):
        name = self.cleaned_data['name']
        if name:
            name_list = name.split()
            if len(name_list) > 1:
                self.cleaned_data['last_name'] = name_list.pop()
                self.cleaned_data['first_name'] = ' '.join(name_list)
            else:
                self.cleaned_data['first_name'] = name


class PassWordResetFromEmail(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    def clean_email(self):
        email = self.cleaned_data['email']
        value = self.get_users(email)
        if not value:
            raise forms.ValidationError("The email is not register.")
        return email

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, email, html_email_template_name=None):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = subject_template_name
        # Email subject *must not* contain newlines
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMessage(subject, body, from_email, [email])
        email_message.content_subtype = "html"
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message = EmailMessage(subject, html_email, from_email, [email])
            email_message.content_subtype = "html"

        email_message.send()

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = get_user_model()._default_manager.filter(
            username=email, is_active=True)
        return active_users

    def save(self, domain_override=None,
             subject_template_name='[ItsCoastal] Reset Password',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["email"]

        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': user.email,
                'domain': settings.SITE_DOMAIN,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                user.email, html_email_template_name=html_email_template_name,
            )
