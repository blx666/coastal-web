from coastal.core import response
from coastal.core.response import JsonResponse
from coastal.apps.product.models import Product, ProductImage
from coastal.apps.product.forms import ProductListForm
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from .uilts import similar_products
from django.forms.models import model_to_dict


def product_list(request):
    form = ProductListForm(request.GET)
    if not form.is_valid():
        return JsonResponse(status=response.STATUS_404, message="The product does not exist.")
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
        product_data = model_to_dict(product, fields=['id','for_rental', 'for_sale', 'rental_price', 'rental_unit', 'beds', 'max_guests'])
        product_data.update({
            "category": product.category_id,
            "images": product.images,
            "sale_price": None,
            "lon": product.point[1],
            "lat": product.point[0],
        })
        data.append(product_data)
    return JsonResponse(data)


def product_detail(request, pid):
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return JsonResponse(status=response.STATUS_404, message="The product does not exist.")
    images = ProductImage.objects.filter(product=product)
    image = [product_image.image.url for product_image in images]
    # owner_name = product.owner.name or 'qwe'
    name = product.name
    description = product.description
    amenities = product.amenities
    address = product.address
    for_rental = product.for_rental
    for_sale = product.for_sale
    rental_price = product.rental_price
    rental_unit = product.rental_unit
    category = product.category.id
    data = {
        "id": pid,
        "category": category,
        "images": image,
        "for_rental": for_rental,
        "for_sale": for_sale,
        "rental_price": rental_price,
        "rental_unit": rental_unit,
        "sale_price": None,
        "address": address,
        "name": name,
        "short_desc": "1,200 ft. Yacht",
        "description": description,
        "Amenities": amenities,
        "liked": False,
        "owner": {
            "id": product.owner.id,
            "name": 'Jam Green',
            "photo": "/media/user/photo001.jpg",
        },
        "reviews": {
            "count": 8,
            "avg_score": 4.3,
            "latest_review": {
                "reviewer_name": "Sandra Ravikal",
                "reviewer_photo": "/media/user/photo012.jpg",
                "stayed_range": "02/27 - 02/28",
                "score": 5,
                "content": "This is a sample rating of this listing."
            }
        },
        "similar_products": similar_products(product)
    }
    return JsonResponse(data)

