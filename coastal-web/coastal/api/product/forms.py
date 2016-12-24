from django import forms
from coastal.apps.product.models import ProductImage, Product


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['owner']


class ProductListFilterForm(forms.Form):
    lon = forms.FloatField()
    lat = forms.FloatField()
    distance = forms.IntegerField()
    guests = forms.IntegerField(required=False)
    arrival_date = forms.DateField(required=False)
    checkout_date = forms.DateField(required=False)
    min_price = forms.DecimalField(required=False)
    max_price = forms.DecimalField(required=False)
    sort = forms.CharField(required=False)
    category = forms.IntegerField(required=False)
    purchase_or_rent = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(ProductListFilterForm, self).clean()
        purchase_or_rent = cleaned_data['purchase_or_rent']
        self.cleaned_data['for_rental'] = purchase_or_rent in ('rent', 'both')
        self.cleaned_data['for_sale'] = purchase_or_rent in ('sale', 'both')


class RentalDateForm(forms.Form):
    arrival_date = forms.DateTimeField()
    checkout_date = forms.DateTimeField()