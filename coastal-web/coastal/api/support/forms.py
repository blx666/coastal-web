from coastal.apps.support.models import Report, Helpcenter
from django import forms


class HelpCenterForm(forms.ModelForm):
    class Meta:
        model = Helpcenter
        fields = ['email', 'subject', 'content']
