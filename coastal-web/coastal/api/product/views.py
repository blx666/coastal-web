from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.forms.models import model_to_dict

from coastal.core import response
from coastal.api.product.forms import ImageUploadForm, ProductForm, ProductListFilterForm
from coastal.api.product.utils import get_similar_products, bond_product_image
from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.product import defines as defs


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)

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
    for_sale = form.cleaned_data['for_sale']
    for_rental = form.cleaned_data['for_rental']
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
        products = products.filter(category=category)
    if min_price:
        products = products.filter(rental_price__gte=min_price)
    if max_price:
        products = products.filter(rental_price__lte=max_price)
    if arrival_date:
        products = products.filter(rentaldaterange__start_date__lte=arrival_date)
    if checkout_date:
        products = products.filter(rentaldaterange__end_date__gte=checkout_date)
    if sort:
        products = products.order_by(sort.replace('price', 'rental_price'))

    bond_product_image(products)
    data = []
    for product in products[0:20]:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit', 'beds',
                                             'max_guests'])
        product_data.update({
            "category": product.category_id,
            "images": product.images,
            "sale_price": None,
            "lon": product.point[1],
            "lat": product.point[0],
        })
        data.append(product_data)
    return CoastalJsonResponse(data)


def product_detail(request, pid):
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")

    data = model_to_dict(product, fields=['category', 'id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit',
                                          'sale_price', 'city', 'max_guests', 'max_guests', 'reviews_count',
                                          'reviews_avg_score', 'liked'])
    if product.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT):
        data['short_desc'] = '%s rooms' % product.rooms
    elif product.category_id == defs.CATEGORY_ROOM:
        data['short_desc'] = 'single room'
    elif product.category_id == defs.CATEGORY_YACHT:
        data['short_desc'] = '%s ft. yacht' % product.length
    elif product.category_id == defs.CATEGORY_JET:
        data['short_desc'] = '%s ft. jet' % product.length

    data['images'] = [i.image.url for i in ProductImage.objects.filter(product=product)]

    data['owner'] = {
        'user_id': product.owner_id,
        'name': product.owner.first_name,
        'photo': "/media/user/photo001.jpg",
    }
    data['reviews'] = {
        "count": 8,
        "avg_score": 4.3,
        "latest_review": {
            "reviewer_name": "Sandra Ravikal",
            "reviewer_photo": "/media/user/photo012.jpg",
            "stayed_range": "02/27 - 02/28",
            "score": 5,
            "content": "This is a sample rating of this listing."
        }
    }

    similar_product_dict = []
    for p in get_similar_products(product):
        content = model_to_dict(p, fields=['id', 'category', 'liked', 'for_rental', 'for_sale', 'rental_price',
                                           'sale_price', 'city', 'max_guests'])
        content['reviews_count'] = 0
        content['reviews_avg_score'] = 0
        content['images'] = bond_product_image(p)
        similar_product_dict.append(content)
    data['similar_products'] = similar_product_dict
    return CoastalJsonResponse(data)


def product_image_upload(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)
    image = form.save()
    data = {
        'image_id': image.id
    }
    return CoastalJsonResponse(data)


def product_add(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=405)

    form = ProductForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)

    product = form.save(commit=False)
    product.owner = request.user
    product.save()
    data = {
        'product_id': product.id
    }
    return CoastalJsonResponse(data)

