from coastal.core import response
from coastal.core.response import JsonResponse
from .models import Product


def product_list(request):
    return JsonResponse()


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
