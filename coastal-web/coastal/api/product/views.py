from coastal.core import response
from coastal.api.product.forms import ImageUploadForm, ProductForm
from coastal.apps.product.models import Product, ProductImage
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance, D
from coastal.api.product.utils import get_similar_products
from django.forms.models import model_to_dict
from coastal.api.core.response import CoastalJsonResponse, JsonResponse


def product_list(request):
    lon = float(request.GET.get('lon'))
    lat = float(request.GET.get('lat'))
    distance = int(request.GET.get('distance'))
    target = Point(lat, lon)
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)))
    data = []
    for product in products[0:20]:
        images = list(ProductImage.objects.filter(product=product))
        data.append({
            "id": product.id,
            "category": product.category.id,
            "images": [product_image.image.url for product_image in images],
            "for_rental": product.for_rental,
            "for_sale": product.for_sale,
            "rental_price": product.rental_price,
            "rental_unit": product.rental_unit,
            "sale_price": None,
            "lon": product.point[1],
            "lat": product.point[0],
            "beds": product.beds,
            "max_guests": product.max_guests,
        })
    return JsonResponse(data)


def product_detail(request, pid):
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")

    data = model_to_dict(product, fields=['category', 'id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit',
                                          'sale_price', 'city', 'max_guests', 'max_guests', 'reviews_count',
                                          'reviews_avg_score', 'liked'])

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
        img_urls = []
        for img_url in p.productimage_set.all():
            img_urls.append(img_url.image.url)
        content['images'] = img_urls
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
