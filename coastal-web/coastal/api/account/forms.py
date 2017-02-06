from django import forms
from django.contrib.auth.models import User
from coastal.apps.account.models import UserProfile


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(min_length=6)
    uuid = forms.CharField(required=False)
    token = forms.CharField(required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('The user have already been used for register')
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
        fields = ['agency_email', 'agency_name', 'agency_address', 'photo']


class CheckEmailForm(forms.Form):
    email = forms.EmailField(required=True)


class FacebookLoginForm(forms.Form):
    userid = forms.CharField()
    email = forms.EmailField()
    name = forms.CharField(max_length=128)
    token = forms.CharField(required=False)
    uuid = forms.CharField(required=False)






