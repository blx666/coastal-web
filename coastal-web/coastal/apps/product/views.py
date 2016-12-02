from coastal.core import response
from coastal.core.response import JsonResponse
from .models import Product, ProductImage
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance, D


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

    data = {
        "id": 12,
        "category": 1,
        "images": ["/media/products/image001.jpg"],
        "for_rental": True,
        "for_sale": True,
        "rental_price": 1023.00,
        "rental_unit": "Day",
        "sale_price": 2050000.00,
        "lon": 35.4340958,
        "lat": -115.6360776,
        "address": "Malibu, CA, United States",
        "name": "Oceanfast",
        "short_desc": "1,200 ft. Yacht",
        "description": "This is a sample description of a beautiful yacht. ",
        "Amenities": "Air conditioning, Hot Tub, TV, Wifi",
        "liked": False,
        "owner": {
            "id": 23,
            "name": "Sarah Keller",
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
        "similar_products": [{
            "id": 28,
            "category": 1,
            "image": "/media/products/image021.jpg",
            "liked": False,
            "for_rental": True,
            "for_sale": False,
            "rental_price": 7500.00,
            "rental_unit": "Day",
            "sale_price": None,
            "city": "Malibu",
            "max_guests": 6,
            "speed": 1200,
            "reviews_count": 8,
            "reviews_avg_score": 4.5,
        }, {}]
    }

    return JsonResponse(data)