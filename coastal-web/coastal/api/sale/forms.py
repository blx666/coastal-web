from django import forms
from coastal.apps.sale.models import SaleOffer


class SaleOfferForm(forms.ModelForm):

    class Meta:
        model = SaleOffer
        fields = ['product', 'conditions', 'price']

    def clean(self):

        product = self.cleaned_data.get('product')
        if not product.for_sale:
                raise forms.ValidationError('the product cannot be sold.')
