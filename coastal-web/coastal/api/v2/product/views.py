from datetime import datetime
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Avg, Count, Q
from django.forms.models import model_to_dict

from coastal.api import defines as defs
from coastal.api.product.forms import ProductListFilterForm
from coastal.api.product.utils import bind_product_image
from coastal.api.product.views import product_add as product_add_v1, product_update as product_update_v1
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.apps.account.models import FavoriteItem
from coastal.apps.product import defines as product_defs
from coastal.apps.product.models import Product
from coastal.apps.currency.utils import price_display


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

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
    products = Product.objects.filter(status='published')

    # address filter
    if poly:
        products = products.filter(point__contained=poly)
    else:
        for key in ('country', 'administrative_area_level_1', 'administrative_area_level_2', 'locality', 'sublocality'):
            if form.cleaned_data[key]:
                products = products.filter(**{key: form.cleaned_data[key]})

    query, query_exp, query_boat_slip = None, None, None
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
            products = products.filter(max_guests__gte=guests)

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
    products = Product.objects.filter(status='published')

    # address filter
    for key in ('country', 'administrative_area_level_1', 'administrative_area_level_2', 'locality', 'sublocality'):
        if request.GET.get(key):
            products = products.filter(**{key: request.GET.get(key)})

    products = products.order_by('-rank', '-score', '-rental_usd_price', '-sale_usd_price')

    bind_product_image(products)
    page = request.GET.get('page', 1)
    item = defs.PER_PAGE_ITEM
    paginator = Paginator(products, item)
    try:
        product_page = paginator.page(page)
    except PageNotAnInteger:
        product_page = paginator.page(1)
    except EmptyPage:
        product_page = paginator.page(paginator.num_pages)

    if int(page) >= paginator.num_pages:
        next_page = 0
    else:
        next_page = int(page) + 1

    liked_product_id_list = []
    if request.user.is_authenticated:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list('product_id',
                                                                                                     flat=True)
    products_list = []
    for product in product_page:
        reviews = product.review_set
        avg_score = reviews.aggregate(Avg('score'), Count('id'))
        data = {
            'type': product.category.name or '',
            'address': product.address or '',
            'reviews_count':  avg_score['id__count'],
            'rental_price': product.rental_price or 0,
            'sale_price': product.sale_price or 0,
            'beds': product.beds or 0,
            'length': product.length or 0,
            'city': product.locality or '',
            'id': product.id,
            'category': product.category_id,
            'liked': product.id in liked_product_id_list,
            'for_rental': product.for_rental or '',
            'for_sale': product.for_sale or '',
            'max_guests': product.max_guests or 0,
            'rental_unit': product.new_rental_unit(),
            'rental_price_display': product.get_rental_price_display(),
            'sale_price_display': product.get_sale_price_display(),
            'reviews_avg_score': avg_score['score__avg'] or 0,
        }
        if product.point:
            data['lon'] = product.point[0]
            data['lat'] = product.point[1]
        if product.images:
            data['image'] = product.images[0].image.url
        else:
            data['image'] = ''
        products_list.append(data)
    result = {
        'count': len(products),
        'products': products_list,
        'next_page': next_page
    }
    return CoastalJsonResponse(result)

