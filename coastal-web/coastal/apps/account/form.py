from django import forms
from django.utils.translation import ugettext_lazy as _


class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': _("The passwords do not match. Please try again."),
    }
    new_password1 = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput,
        error_messages={'min_length': 'Password should be at least 6 characters.'},
    )
    new_password2 = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput,
        error_messages={'min_length': 'Password should be at least 6 characters.'},
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
