from coastal.core import response
from coastal.core.response import JsonResponse
from .models import Product, ProductImage
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance, D
from .uilts import similar_products


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

