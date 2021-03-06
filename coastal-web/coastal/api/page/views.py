from django.forms.models import model_to_dict
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.db.models import Avg, Count
from django.views.decorators.cache import cache_page

from coastal.api.core.response import CoastalJsonResponse
from coastal.apps.promotion.models import HomeBanner
from coastal.apps.product.models import Product, ProductImage
from coastal.api.product.utils import bind_product_main_image
from coastal.apps.account.models import FavoriteItem
from coastal.api import defines as defs
from coastal.apps.product import defines as product_defs
from coastal.apps.review.models import Review
from coastal.core import cache_defines as cache_keys


def home(request):
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1

    product_list, next_page = get_home_product_list(page)

    liked_product_id_list = []
    if request.user.is_authenticated:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
            'product_id', flat=True)
    for p in product_list:
        p['liked'] = p['id'] in liked_product_id_list

    result = {
        'home_banner': get_home_banners(),
        'products': product_list,
        'next_page': next_page
    }
    return CoastalJsonResponse(result)


def get_home_banners():
    home_banners_list = cache.get(cache_keys.CACHE_HOME_BANNER_KEY)

    if home_banners_list is not None:
        return home_banners_list

    home_banners_list = []

    for banner in HomeBanner.objects.order_by('display_order'):
        banner_dict = {
            'city_name': banner.city_name,
            'image': banner.image.url,
            'address_info': {
                'country': banner.country or '',
                'administrative_area_level_1': banner.state or '',
                'administrative_area_level_2': banner.county or '',
                'locality': banner.locality or '',
                'sublocality': banner.sublocality or '',
            },
        }
        if banner.point:
            banner_dict.update({
                'lon': banner.point[0],
                'lat': banner.point[1],
            })

        home_banners_list.append(banner_dict)

    cache.set(cache_keys.CACHE_HOME_BANNER_KEY, home_banners_list, cache_keys.CACHE_TIME)

    return home_banners_list


def get_home_product_list(page):
    """
    :param page: int
    :return:
    """
    home_product_list_result = cache.get(cache_keys.CACHE_HOME_PRODUCT_LIST_KEY % page)

    if home_product_list_result is not None:
        return home_product_list_result

    published_product_query = Product.objects.filter(status='published').order_by(
        '-rank', '-score', '-rental_usd_price', '-sale_usd_price')
    space_products = published_product_query.filter(category__in=product_defs.SPACE_CATEGORY_LIST)
    yacht_products = published_product_query.filter(category__in=product_defs.YACHT_CATEGORY_LIST)
    adventure_products = published_product_query.filter(category=product_defs.CATEGORY_ADVENTURE)

    products = []
    space_count, yacht_count, adventure_count = space_products.count(), yacht_products.count(), adventure_products.count()
    count = max(space_count, yacht_count, adventure_count)
    for i in range(count):
        if i < space_count:
            products.append(space_products[i])
        if i < yacht_count:
            products.append(yacht_products[i])
        if i < adventure_count:
            products.append(adventure_products[i])

    paginator = Paginator(products, defs.PER_PAGE_ITEM)
    try:
        cur_page = paginator.page(page)
    except EmptyPage:
        cur_page = paginator.page(paginator.num_pages)

    product_list = []

    cur_page_products = cur_page.object_list
    bind_product_main_image(cur_page_products)
    for product in cur_page_products:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_price', 'sale_price'])
        product_data.update({
            'max_guests': product.max_guests or 0,
            'length': product.length or 0,
            'beds': product.beds or 0,
            "category": product.category_id,
            'rental_unit': product.new_rental_unit(),
            'rental_price_display': product.get_rental_price_display(),
            'sale_price_display': product.get_sale_price_display(),
            'city': product.locality or '',
        })

        product_data['image'] = product.main_image and product.main_image.image.url or ''
        reviews = Review.objects.filter(product=product)
        avg_score = reviews.aggregate(Avg('score'), Count('id'))
        product_data['reviews_count'] = avg_score['id__count']
        product_data['reviews_avg_score'] = avg_score['score__avg'] or 0
        if product.point:
            product_data.update({
                "lon": product.point[0],
                "lat": product.point[1],
            })
            product_list.append(product_data)

    if page >= paginator.num_pages:
        next_page = 0
    else:
        next_page = page + 1

    cache.set(cache_keys.CACHE_HOME_PRODUCT_LIST_KEY % page, (product_list, next_page), cache_keys.CACHE_TIME)

    return product_list, next_page


@cache_page(5 * 60)
def images_360(request):
    images_view = ProductImage.objects.filter(image_type='360-view', product__status='published').order_by('-product__score')[0:90]

    image_list = []
    for image_360 in images_view:
        image_info = {
            'product_id': image_360.product_id,
            'for_rental': image_360.product.for_rental,
            'for_sale': image_360.product.for_sale,
            'rental_price': image_360.product.rental_price,
            'sale_price': image_360.product.sale_price,
            'currency': image_360.product.currency,
            'rental_unit': image_360.product.rental_unit,
            'rental_unit_display': image_360.product.get_rental_unit_display(),
            'image': image_360.image.url,
            'name': image_360.product.name,
            'rental_price_display': image_360.product.get_rental_price_display(),
            'sale_price_display': image_360.product.get_sale_price_display(),
        }
        image_list.append(image_info)

    result = []
    for i in image_list:
        if i['product_id'] not in [p['product_id'] for p in result]:
            result.append(i)

    return CoastalJsonResponse(result[0:30])
