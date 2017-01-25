from django import forms
from coastal.apps.sale.models import SaleOffer


class SaleOfferForm(forms.ModelForm):

    class Meta:
        model = SaleOffer
        fields = ['product', 'conditions', 'price']

    def clean(self):
        product = self.cleaned_data.get('product')
        if product and not product.for_sale:
            raise forms.ValidationError('the product cannot be sold.')


class SaleApproveForm(forms.Form):
    approve = forms.CharField()
    note = forms.CharField(required=False)

    def clean_approve(self):
        value = self.cleaned_data.get('approve')
        if value not in ('0', '1'):
            raise forms.ValidationError("The value should be boolean: 0/1")
        return value == '1'
