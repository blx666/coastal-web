from datetime import datetime
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Avg, Count, Q
from django.forms.models import model_to_dict
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from django.core.cache import cache

from coastal.api import defines as defs
from coastal.api.product.forms import ProductListFilterForm, ProductSearchFilterForm
from coastal.api.product.views import product_add as product_add_v1, product_update as product_update_v1
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import FavoriteItem
from coastal.apps.product import defines as product_defs
from coastal.apps.product.models import Product, ProductImage, Amenity
from coastal.apps.currency.utils import price_display
from coastal.apps.review.models import Review
from coastal.api.product.utils import get_similar_products, bind_product_image, count_product_view, \
    get_product_discount, bind_product_main_image
from coastal.apps.account.models import RecentlyViewed


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    products = _advance_filter_product(form)

    bind_product_image(products)

    page = request.GET.get('page', 1)
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

    data = []

    for product in products:
        if product.category_id == product_defs.CATEGORY_ADVENTURE:
            product_data = model_to_dict(product,
                                         fields=['id', 'exp_time_unit', 'exp_time_length'])
            product_data.update({
                'rental_price': product.rental_price,
                'rental_price_display': price_display(product.rental_price, product.currency),
                'exp_time_unit': product.exp_time_unit,
                'max_guests': product.max_guests or 0,
        })
        elif product.category_id == product_defs.CATEGORY_BOAT_SLIP:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'length',
                                                 'max_guests'])
            if not product.length:
                product_data['length'] = 0
        else:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'beds',
                                                 'max_guests'])
        if product.for_rental and product.category_id != product_defs.CATEGORY_ADVENTURE:
            product_data.update({
                'rental_price': int(product.get_price('day')),
                'rental_unit': 'Day',
                'rental_price_display': price_display(int(product.get_price('day')), product.currency),
        })
            rental_price = product.rental_price
            if product.rental_unit == "half-day":
                rental_price *= 4
            if product.rental_unit == 'hour':
                rental_price *= 24
        if product.for_sale and product.category_id != product_defs.CATEGORY_ADVENTURE:
            product_data.update({
                'sale_price': product.sale_price,
                'sale_price_display': product.get_sale_price_display(),
        })

        product_data.update({
            "category": product.category_id,
            "images": [i.image.url for i in product.images],
            "lon": product.point[0],
            "lat": product.point[1],
        })
        data.append(product_data)
    result = {
        'next_page': next_page,
        'products': data,
    }
    return CoastalJsonResponse(result)


@login_required
def product_add(request):
    return product_add_v1(request)


@login_required
def product_update(request):
    return product_update_v1(request)


def product_search(request):
    form = ProductSearchFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    # address filter
    products = _advance_filter_product(form)

    bind_product_main_image(products)

    page = request.GET.get('page', 1)
    item = defs.PER_PAGE_ITEM
    paginator = Paginator(products, item)
    try:
        product_page = paginator.page(page)
    except PageNotAnInteger:
        product_page = paginator.page(1)
    except EmptyPage:
        product_page = paginator.page(paginator.num_pages)

    lon = form.cleaned_data.get('lon')
    lat = form.cleaned_data.get('lat')
    nearby_products_list = []
    if int(page) >= paginator.num_pages:
        if lon and lat:
            nearby_products = get_nearby_products(lon, lat, products)
            bind_product_main_image(nearby_products)
            nearby_products_list = generate_product_data(nearby_products)

        next_page = 0
    else:
        next_page = int(page) + 1

    liked_product_id_list = []
    if request.user.is_authenticated:
        user = request.user
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=user).values_list(
                'product_id', flat=True)
    products_list = generate_product_data(product_page)

    for product in products_list:
        product['liked'] = product['id'] in liked_product_id_list

    result = {
        'count': len(products),
        'products': products_list,
        'next_page': next_page,
        'nearby_products_list': nearby_products_list
    }
    return CoastalJsonResponse(result)


def _advance_filter_product(form):
    arrival_date = form.cleaned_data['arrival_date']
    checkout_date = form.cleaned_data['checkout_date']
    min_price = form.cleaned_data['min_price']
    max_price = form.cleaned_data['max_price']
    sort = form.cleaned_data['sort']
    category = form.cleaned_data['category']
    category_exp = form.cleaned_data.get('category_exp')
    category_boat_slip = form.cleaned_data.get('category_boat_slip')
    category_empty = form.cleaned_data.get('category_empty')
    for_sale = form.cleaned_data['for_sale']
    for_rental = form.cleaned_data['for_rental']
    max_coastline_distance = form.cleaned_data['max_coastline_distance']
    min_coastline_distance = form.cleaned_data['min_coastline_distance']
    guests = form.cleaned_data['guests']
    poly = form.cleaned_data.get('poly')
    poly2 = form.cleaned_data.get('poly2')

    query, query_exp, query_boat_slip = None, None, None

    products = Product.objects.filter(status='published')

    if poly:
        if poly2:
            products = products.filter(Q(point__within=poly) | Q(point__within=poly2))
        else:
            products = products.filter(point__within=poly)
    else:
        for key in ('country', 'administrative_area_level_1', 'administrative_area_level_2', 'locality', 'sublocality'):
            if form.cleaned_data[key]:
                products = products.filter(**{key: form.cleaned_data[key]})

    if category:
        query = Q(category__in=category)
        if for_rental and not for_sale:
            query &= Q(for_rental=True)
        elif for_sale and not for_rental:
            query &= Q(for_sale=True)
        if min_price:
            query &= Q(**{"%s__gte" % form.cleaned_data['price_field']: min_price})
        if max_price:
            query &= Q(**{"%s__lte" % form.cleaned_data['price_field']: max_price})
        if guests:
            query &= Q(max_guests__gte=guests)
    if category_exp:
        query_exp = Q(category=category_exp)
        if min_price:
            query_exp &= Q(rental_usd_price__gte=min_price)
        if max_price:
            query_exp &= Q(rental_usd_price__lte=max_price)
        if guests:
            query_exp &= Q(max_guests__gte=guests)
    if category_boat_slip:
        query_boat_slip = Q(category=category_boat_slip)
        if for_rental and not for_sale:
            query_boat_slip &= Q(for_rental=True)
        elif for_sale and not for_rental:
            query_boat_slip &= Q(for_sale=True)
        if min_price:
            query_boat_slip &= Q(**{"%s__gte" % form.cleaned_data['price_field']: min_price})
        if max_price:
            query_boat_slip &= Q(**{"%s__lte" % form.cleaned_data['price_field']: max_price})

    query2 = None
    for q in (query, query_exp, query_boat_slip):
        if q:
            if not query2:
                query2 = q
            else:
                query2 |= q
    if query2:
        products = products.filter(query2)

    if category_empty:
        if for_rental and not for_sale:
            products = products.filter(for_rental=True)
        elif for_sale and not for_rental:
            products = products.filter(for_sale=True)
        if min_price:
            products = products.filter(rental_usd_price__gte=min_price)
        if max_price:
            products = products.filter(rental_usd_price__lte=max_price)
        if guests:
            products = products.filter(Q(max_guests__gte=guests) | Q(category=product_defs.CATEGORY_BOAT_SLIP))

    if arrival_date or checkout_date:
        products = products.exclude(for_rental=False)
    if arrival_date and checkout_date:
        products = products.exclude(blackoutdate__start_date__lte=arrival_date,
                                    blackoutdate__end_date__gte=checkout_date).exclude(
            rentaloutdate__start_date__lte=arrival_date, rentaloutdate__end_date__gte=checkout_date)
    elif checkout_date:
        arrival_date = datetime.now().replace(hour=0, minute=0, second=0)
        products = products.exclude(blackoutdate__start_date__lte=arrival_date,
                                    blackoutdate__end_date__gte=checkout_date).exclude(
            rentaloutdate__start_date__lte=arrival_date, rentaloutdate__end_date__gte=checkout_date)

    if max_coastline_distance and min_coastline_distance:
        products = products.filter(distance_from_coastal__gte=min_coastline_distance,
                                    distance_from_coastal__lte=max_coastline_distance)
    elif min_coastline_distance:
        products = products.filter(distance_from_coastal__gte=min_coastline_distance)
    elif max_coastline_distance:
        products = products.filter(distance_from_coastal__lte=max_coastline_distance)
    if sort:
        products = products.order_by(sort.replace('price', 'rental_price'))
    else:
        products = products.order_by('-rank', '-score', '-rental_usd_price', '-sale_usd_price')
    return products


def get_nearby_products(lon, lat, origin_products):
    point = Point(lon, lat, srid=4326)
    distance_range = (defs.NEARBY_DISTANCE, defs.NEARBY_DISTANCE+100, defs.NEARBY_DISTANCE+200)
    for v in range(len(distance_range)):
        products = Product.objects.filter(status='published', point__distance_lte=(point, D(mi=distance_range[v]))).exclude(id__in=origin_products).order_by(Distance('point', point))[0:20]
        if products.count() >= 20:
            return products
        if v == len(distance_range)-1 and not products:
            products = Product.objects.filter(status='published').exclude(id__in=origin_products).order_by(Distance('point', point))[0:20]
            return products


def generate_product_data(products):
    _product_list = []
    for product in products:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_price',
                                             'sale_price'])
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
            _product_list.append(product_data)
    return _product_list


def product_detail(request, pid):
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")

    liked_product_id_list = []
    if request.POST.get('preview') != '1':
        count_product_view(product)
        if request.user.is_authenticated():
            user = request.user
            liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
                'product_id', flat=True)

            if RecentlyViewed.objects.filter(user=user, product=product):
                RecentlyViewed.objects.filter(user=user, product=product).update(date_created=datetime.now())
            else:
                RecentlyViewed.objects.create(user=user, product=product, date_created=datetime.now())

    if product.category_id == product_defs.CATEGORY_ADVENTURE:
        data = model_to_dict(product, fields=['id', 'max_guests', 'exp_time_length', 'category', 'currency'])
        data['exp_start_time'] = product.exp_start_time and product.exp_start_time.strftime('%I:%M %p') or ''
        if product.check_exp_end_time():
            data['exp_end_time'] = '12:00 AM'
        else:
            data['exp_end_time'] = product.exp_end_time and product.exp_end_time.strftime('%I:%M %p') or ''
        data['exp_time_unit'] = product.get_exp_time_unit_display()
        data['city'] = product.locality or ''
    else:
        data = model_to_dict(product, fields=['category', 'id', 'for_rental', 'for_sale', 'sale_price', 'currency'])
        data['city'] = product.locality or ''
    if product.max_guests:
        data['max_guests'] = product.max_guests

    if product.category_id in (product_defs.CATEGORY_HOUSE, product_defs.CATEGORY_APARTMENT):
        data['room'] = product.rooms or 0
        data['bathrooms'] = product.bathrooms or 0
    if product.category_id in (product_defs.CATEGORY_ROOM, product_defs.CATEGORY_YACHT):
        data['beds'] = product.beds or 0
        data['bathrooms'] = product.bathrooms or 0

    if product.point:
        data['lon'] = product.point[0]
        data['lat'] = product.point[1]
    if product.get_amenities_display():
        data['amenities'] = product.get_amenities_display()
    data['short_desc'] = product.short_desc
    if product.new_rental_unit():
        data['rental_unit'] = product.new_rental_unit()
    else:
        data['rental_unit'] = 'Day'
    if product.description:
        data['description'] = product.description
    else:
        data['description'] = 'Description'
    if product.rental_price:
        data['rental_price'] = product.rental_price
    else:
        data['rental_price'] = 0
    data['liked'] = product.id in liked_product_id_list
    data['rental_price_display'] = product.get_rental_price_display()
    data['sale_price_display'] = product.get_sale_price_display()
    data['city_address'] = product.city_address or ''
    images = []
    views = []
    for pi in ProductImage.objects.filter(product=product):
        if pi.caption != ProductImage.CAPTION_360:
            images.append(pi.image.url)
        else:
            views.append(pi.image.url)

    data['images_360'] = views
    data['images'] = images
    if product.name:
        data['name'] = product.name
    else:
        data['name'] = 'Your Listing Name'
    data['owner'] = {
        'user_id': product.owner_id,
        'name': product.owner.basic_info()['name'],
        'photo': product.owner.basic_info()['photo'],
        'purpose': product.owner.userprofile.purpose,
    }
    reviews = Review.objects.filter(product=product).order_by('-date_created')
    last_review = reviews.first()
    avg_score = reviews.aggregate(Avg('score'), Count('id'))
    data['reviews'] = {
        'count': avg_score['id__count'],
        'avg_score': avg_score['score__avg'] or 0,
    }
    if last_review:
        start_time = last_review.order.start_datetime
        end_time = last_review.order.end_datetime
        data['reviews']['latest_review'] = {
            "stayed_range": '%s - %s' % (datetime.strftime(start_time, '%Y/%m/%d'), datetime.strftime(end_time, '%Y/%m/%d')),
            "score": last_review.score,
            "content": last_review.content
        }
        data['reviews']['latest_review'].update(last_review.owner.basic_info(prefix='reviewer_'))
    data['extra_info'] = {
        'rules': {
            'name': '%s Rules' % product.category.name,
            'content': product.rental_rule or 'Nothing is set',
        },
        'cancel_policy': {
            'name': 'Cancellation Policy',
            'content': 'Coastal does not provide online cancellation service. Please contact us if you have any needs.'
        },
    }

    if product.for_rental and product.category_id != product_defs.CATEGORY_ADVENTURE:
        price = get_product_discount(product.rental_price, product.rental_unit, product.discount_weekly, product.discount_monthly)
        discount = {
            'discount': {
                'name': 'Additional Price',
                'weekly_discount': product.discount_weekly or 0,
                'updated_weekly_price': price[0],
                'updated_weekly_price_display': price_display(price[0], product.currency),
                'monthly_discount': product.discount_monthly or 0,
                'updated_monthly_price': price[1],
                'updated_monthly_price_display': price_display(price[1], product.currency),
            }
        }
    else:
        discount = {
            'discount': {}
        }
    data.get('extra_info').update(discount)

    similar_product_dict = cache.get('similar_products|%s' % product.id)
    if similar_product_dict is None:
        similar_products = get_similar_products(product)
        bind_product_main_image(similar_products)
        similar_product_dict = generate_product_data(similar_products)

        cache.set('similar_products|%s' % product.id, similar_product_dict, 5 * 60)

    for product in similar_product_dict:
        product['liked'] = product['id'] in liked_product_id_list

    data['similar_products'] = similar_product_dict
    return CoastalJsonResponse(data)
