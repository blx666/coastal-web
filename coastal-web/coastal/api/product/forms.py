from django import forms
from coastal.apps.product.models import ProductImage, Product, Amenity
from django.contrib.gis.geos import Point


class ImageUploadForm(forms.ModelForm):
    pid = forms.FloatField(required=False)

    class Meta:
        model = ProductImage
        fields = ['image', 'caption']


class ProductAddForm(forms.ModelForm):
    lon = forms.FloatField(required=False)
    lat = forms.FloatField(required=False)
    amenities = forms.CharField(required=False)
    images = forms.CharField(required=False)
    for_sale = forms.CharField(required=False)
    for_rental = forms.CharField(required=False)

    def clean_amenities(self):
        value = self.cleaned_data.get('amenities')
        if not value:
            return []

        amenities = []
        try:
            for i in value.split(','):
                amenities.append(Amenity.objects.get(id=int(i)))
        except Amenity.DoesNotExist:
            raise forms.ValidationError('The amenity does not exist.')
        except:
            raise forms.ValidationError('The amenities value is invalid.')
        return amenities

    def clean_images(self):
        value = self.cleaned_data.get('images')
        if not value:
            return []

        images = []
        try:
            for i in value.split(','):
                images.append(ProductImage.objects.get(id=int(i)))
        except ProductImage.DoesNotExist:
            raise forms.ValidationError('The product image does not exist.')
        except:
            raise forms.ValidationError('The images value is invalid.')
        return images

    def clean_for_rental(self):
        value = self.cleaned_data.get('for_rental')
        if value:
            if value not in ('0', '1'):
                raise forms.ValidationError("The value should be boolean: 0/1")
            return value == '1'

    def clean_for_sale(self):
        value = self.cleaned_data.get('for_sale')
        if value:
            if value not in ('0', '1'):
                raise forms.ValidationError("The value should be boolean: 0/1")
            return value == '1'

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
        exclude = ['owner', 'score']


class ProductUpdateForm(ProductAddForm):
    action = forms.CharField()

    def clean(self):
        for key in self.cleaned_data.copy():
            if key not in self.data:
                self.cleaned_data.pop(key)

    class Meta:
        model = Product
        exclude = ['owner', 'score']


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
