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
    photo = forms.ImageField(max_length=255, required=False)

    class Meta:
        model = UserProfile
        fields = ['is_agent', 'agency_email', 'agency_name', 'agency_address', 'photo']


class CheckEmailForm(forms.Form):
    email = forms.EmailField(required=True)

