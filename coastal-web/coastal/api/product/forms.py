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
