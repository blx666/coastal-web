from coastal.core import response
from coastal.core.response import JsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.api.product.forms import ProductListForm
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
# from .uilts import similar_products
from django.forms.models import model_to_dict
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE


def product_list(request):
    form = ProductListForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(status=400)
    lon = form.cleaned_data['lon']
    lat = form.cleaned_data['lat']
    distance = form.cleaned_data['distance']
    target = Point(lat, lon)
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)))
    product_images = ProductImage.objects.filter(product__in=products)
    for product in products:
        product.images = []
        for image in product_images:
            if image.product == product:
                product.images.append(image.image.url)
    data = []
    for product in products[0:20]:
        product_data = model_to_dict(product, fields=['id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit', 'beds', 'max_guests'])
        product_data.update({
            "category": product.category_id,
            "images": product.images,
            "sale_price": None,
            "lon": product.point[1],
            "lat": product.point[0],
        })
        data.append(product_data)
    return CoastalJsonResponse(data)