from django import forms
from coastal.apps.rental.models import RentalOrder
from coastal.apps.product.models import Product


class RentalBookForm(forms.ModelForm):

    class Meta:
        model = RentalOrder
        fields = ['guest_count', 'start_datetime', 'end_datetime', 'rental_unit', 'product']

    def clean(self):
        unit_mapping = {
            'day': 24,
            'half-day': 6,
            'hour': 1
        }
        unit = self.cleaned_data.get('rental_unit')
        product = self.cleaned_data.get('product')
        if unit and product:
            if unit_mapping[unit] < unit_mapping[product.rental_unit]:
                raise forms.ValidationError('the rental_unit is invalid.')


class RentalApproveForm(forms.Form):
    approve = forms.CharField()
    note = forms.CharField(required=False)

    def clean_approve(self):
        value = self.cleaned_data.get('approve')
        if value not in ('0', '1'):
            raise forms.ValidationError("The value should be boolean: 0/1")
        return value == '1'

