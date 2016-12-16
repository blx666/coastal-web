from django.forms.models import model_to_dict

from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.promotion.models import HomeBanner
from coastal.apps.product.models import Product
from coastal.api.product.utils import bind_product_image


def home(request):
    home_banners = HomeBanner.objects.all()
    products = Product.objects.order_by('-score')
    show_products = products[0:50]
    data = []
    total_banners = []
    total_products = []
    for banner in home_banners:
        banners = model_to_dict(banner, fields=['city_name', 'display_order'])
        banners.update({
            'image': banner.image.url,
            'lon': banner.point[0],
            'lat': banner.point[1],
        })
        total_banners.append(banners)

    bind_product_image(show_products)

    for product in show_products:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit', 'beds',
                                             'max_guests', 'sale_price'])
        product_data.update({
            "category": product.category_id,
            "images": [i.image.url for i in product.images],
        })
        if product.point:
            product_data.update({
                "lon": product.point[0],
                "lat": product.point[1],
            })
        total_products.append(product_data)

    data.append({
        'home_banner': total_banners,
        'products': total_products,
    })
    return CoastalJsonResponse(data)


def images(request):
    return CoastalJsonResponse()