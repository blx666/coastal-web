from django import forms
from coastal.apps.rental.models import RentalOrder


class RentalBookForm(forms.ModelForm):
    product_id = forms.IntegerField(required=True)

    class Meta:
        model = RentalOrder
        fields = ['guest_count', 'start_datetime', 'end_datetime']


class RentalApproveForm(forms.Form):
    approve = forms.CharField()
    note = forms.CharField(required=False)

    def clean_approve(self):
        value = self.cleaned_data.get('approve')
        if value not in ('0', '1'):
            raise forms.ValidationError("The value should be boolean: 0/1")
        return value == '1'

