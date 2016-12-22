from django.forms.models import model_to_dict

from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.promotion.models import HomeBanner
from coastal.apps.product.models import Product, ProductImage
from coastal.api.product.utils import bind_product_image
from coastal.apps.account.models import FavoriteItem


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
                                             'max_guests', 'sale_price', 'city'])
        product_data.update({
            "category": product.category_id,
        })
        liked_product_id_list = []
        if request.user.is_authenticated:
            liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
                'product_id', flat=True)

        product_data['liked'] = product.id in liked_product_id_list
        if product.images:
            product_data['image'] = [i.image.url for i in product.images][0]
        else:
            product_data['image'] = None
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
    images_view = ProductImage.objects.filter(caption='360-view').order_by('-product__score')[0:30].values(
        'product__for_rental', 'product__for_sale', 'product__rental_price', 'product__rental_unit',
        'product__sale_price', 'product__id', 'image')
    data = []
    for image_360 in images_view:
        image_360['product_id'] = image_360['product__id']
        image_360['for_rental'] = image_360['product__for_rental']
        image_360['for_sale'] = image_360['product__for_sale']
        image_360['rental_price'] = image_360['product__rental_price']
        image_360['rental_unit'] = image_360['product__rental_unit']
        image_360['sale_price'] = image_360['product__sale_price']
        image_360['image_url'] = image_360['image']
        image_360['currency'] = 'USD'
        image_360.pop('product__for_rental')
        image_360.pop('product__for_sale')
        image_360.pop('product__rental_price')
        image_360.pop('product__rental_unit')
        image_360.pop('product__sale_price')
        image_360.pop('product__id')
        image_360.pop('image')
        data.append(image_360)
    return CoastalJsonResponse(data)
