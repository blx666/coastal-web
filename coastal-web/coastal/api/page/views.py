from django.forms.models import model_to_dict

from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.promotion.models import HomeBanner
from coastal.apps.product.models import Product
from coastal.api.product.utils import bind_product_image


def home(request):
    # get home_banner
    home_banners = HomeBanner.objects.order_by('display_order')
    home_banners_list = []
    for banner in home_banners:
        home_banners_list.append({
            'city_name': banner.city_name,
            'image': banner.image.url,
            'lon': banner.point[0],
            'lat': banner.point[1],
        })

    # get recommended products
    products = Product.objects.order_by('-score')[:50]
    bind_product_image(products)
    product_list = []
    for product in products:
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
            product_list.append(product_data)

    result = {
        'home_banner': home_banners_list,
        'products': product_list,
    }
    return CoastalJsonResponse(result)


def images(request):
    return CoastalJsonResponse()