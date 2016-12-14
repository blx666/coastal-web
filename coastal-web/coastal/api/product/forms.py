from django import forms
from coastal.apps.product.models import ProductImage, Product
from django.contrib.gis.geos import Point


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']


class ProductForm(forms.ModelForm):
    lon = forms.FloatField(required=False)
    lat = forms.FloatField(required=False)

    def clean(self):
        lon = self.cleaned_data.get('lon')
        lat = self.cleaned_data.get('lat')
        if lon and lat:
            try:
                self.cleaned_data['point'] = Point(lon, lat)
            except:
                raise forms.ValidationError('lon or lat is invalid.')

    class Meta:
        model = Product
        exclude = ['owner', 'liker', 'viewer', 'amenities']


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
