from coastal.core import response
from coastal.core.response import JsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.api.product.forms import ProductListFilterForm
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
# from .uilts import similar_products
from django.forms.models import model_to_dict
from coastal.api.core.response import CoastalJsonResponse, STATUS_CODE


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(status=400)

    lon = form.cleaned_data['lon']
    lat = form.cleaned_data['lat']
    distance = form.cleaned_data['distance']

    guests = form.cleaned_data['guests']
    arrival_date = form.cleaned_data['arrival_date']
    checkout_date = form.cleaned_data['checkout_date']
    min_price = form.cleaned_data['min_price']
    max_price = form.cleaned_data['max_price']
    sort = form.cleaned_data['sort']
    category = form.cleaned_data['category']
    for_rental = form.cleaned_data['for_rental']
    for_sale = form.cleaned_data['for_sale']
    target = Point(lat, lon)
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)))

    if guests:
        products = products.filter(max_guests__gte=guests)
    if for_sale and for_rental:
        products = products.filter(for_rental=True) | products.filter(for_sale=True)
    elif for_rental:
        products = products.filter(for_rental=True)
    elif for_sale:
        products = products.filter(for_sale=True)
    if category:
        products = products.filter(category__name=category)
    if min_price:
        products = products.filter(rental_price__gte=min_price)
    if max_price:
        products = products.filter(rental_price__lte=max_price)
    if arrival_date:
        products = products.filter(rentaldaterange__start_date__lte=arrival_date)
    if checkout_date:
        products = products.filter(rentaldaterange__end_date__gte=checkout_date)
    if sort == 'price':
        products = products.order_by('rental_price')
    if sort == '-price':
        products = products.order_by('-rental_price')
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