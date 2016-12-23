from django import forms
from django.contrib.auth.models import User
from coastal.apps.account.models import UserProfile


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=6)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('The user have already been used for register')
        return email

    class Meta:
        model = User
        fields = ['email', 'password']


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=128, required=False)
    last_name = forms.CharField(max_length=128, required=False)
    is_agent = forms.CharField(required=False)

    def clean_is_agent(self):
        # TODO: is_agent is not required
        value = self.cleaned_data['is_agent']
        if value not in ('0', '1'):
            raise forms.ValidationError("The value should be boolean: 0/1")
        return value == '1'

    class Meta:
        model = UserProfile
        fields = ['agency_email', 'agency_name', 'agency_address', 'photo']


class CheckEmailForm(forms.Form):
    email = forms.EmailField(required=True)

