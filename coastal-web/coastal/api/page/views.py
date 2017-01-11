from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.views.decorators.cache import cache_page

from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.promotion.models import HomeBanner
from coastal.apps.product.models import Product, ProductImage
from coastal.api.product.utils import bind_product_image
from coastal.apps.account.models import FavoriteItem
from coastal.api import defines as defs


def home(request):
    page = request.GET.get('page', '1')
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
    products = Product.objects.order_by('-score')
    bind_product_image(products)
    item = defs.PER_PAGE_ITEM
    paginator = Paginator(products, item)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    if int(page) >= paginator.num_pages:
        next_page = 0
    else:
        next_page = int(page) + 1
    product_list = []
    for product in products:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_price', 'beds',
                                             'max_guests', 'sale_price', 'city'])
        product_data.update({
            "category": product.category_id,
            'rental_unit': product.get_rental_unit_display(),
            'rental_price_display': product.get_rental_price_display(),
            'sale_price_display': product.get_sale_price_display(),
        })
        liked_product_id_list = []
        if request.user.is_authenticated:
            liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
                'product_id', flat=True)

        product_data['liked'] = product.id in liked_product_id_list
        if product.images:
            product_data['image'] = [i.image.url for i in product.images][0]
        else:
            product_data['image'] = ""
        if product.point:
            product_data.update({
                "lon": product.point[0],
                "lat": product.point[1],
            })
            product_list.append(product_data)

    result = {
        'home_banner': home_banners_list,
        'products': product_list,
        'next_page': next_page
    }
    return CoastalJsonResponse(result)


@cache_page(5 * 60)
def images_360(request):
    images_view = ProductImage.objects.filter(caption='360-view').order_by('-product__score')[0:30]
    data = []
    for image_360 in images_view:
        content = {
            'product_id': image_360.product_id,
            'for_rental': image_360.product.for_rental,
            'for_sale': image_360.product.for_sale,
            'rental_price': image_360.product.rental_price,
            'sale_price': image_360.product.sale_price,
            'currency': image_360.product.currency,
            'rental_unit': image_360.product.rental_unit,
            'image': image_360.image.url,
            'name': image_360.product.name,
            'rental_price_display': image_360.product.get_rental_price_display(),
            'sale_price_display': image_360.product.get_sale_price_display(),
        }
        data.append(content)
    return CoastalJsonResponse(data)
