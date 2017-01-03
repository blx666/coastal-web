import math
import datetime
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.conf import settings

from coastal.api.product.forms import ImageUploadForm, ProductAddForm, ProductUpdateForm, ProductListFilterForm, \
    DiscountCalculatorFrom, RentalDateForm
from coastal.api.product.utils import get_similar_products, bind_product_image, count_product_view, get_product_discount
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.apps.product.models import Product, ProductImage, Amenity
from coastal.apps.account.models import FavoriteItem, Favorites, RecentlyViewed
from coastal.apps.currency.models import Currency
from coastal.apps.rental.models import BlackOutDate, RentalOrder
from coastal.apps.product import defines as defs


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    lon = form.cleaned_data['lon']
    lat = form.cleaned_data['lat']
    distance = form.cleaned_data['distance']

    guests = form.cleaned_data['guests']
    arrival_date = form.cleaned_data['arrival_date']
    checkout_date = form.cleaned_data['checkout_date']
    min_price = form.cleaned_data['min_price']
    max_price = form.cleaned_data['max_price']
    sort = form.cleaned_data['sort']
    category = form.cleaned_data['category']
    for_sale = form.cleaned_data['for_sale']
    for_rental = form.cleaned_data['for_rental']
    if not (lon and lat and distance):
        return recommend_product_list(request)
    target = Point(lon, lat)
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)))
    if not products:
        return recommend_product_list(request)
    if guests:
        products = products.filter(max_guests__gte=guests)
    if for_sale and for_rental:
        products = products.filter(for_rental=True) | products.filter(for_sale=True)
    elif for_rental:
        products = products.filter(for_rental=True)
    elif for_sale:
        products = products.filter(for_sale=True)
    if category:
        products = products.filter(category=category)
    if min_price:
        products = products.filter(rental_price__gte=min_price)
    if max_price:
        products = products.filter(rental_price__lte=max_price)
    if arrival_date:
        products = products.filter(rentaldaterange__start_date__lte=arrival_date)
    if checkout_date:
        products = products.filter(rentaldaterange__end_date__gte=checkout_date)
    if sort:
        products = products.order_by(sort.replace('price', 'rental_price'))
    bind_product_image(products)
    page = request.GET.get('page', 1)
    item = settings.PER_PAGE_ITEM
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
        if product.category_id == defs.CATEGORY_BOAT_SLIP:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'length',
                                                 'max_guests', 'sale_price'])
            if not product.length:
                product_data['length'] = 0
        else:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'beds',
                                                 'max_guests', 'sale_price'])
        rental_price = product.rental_price
        if product.rental_unit == "half-day":
            rental_price *= 4
        if product.rental_unit == 'hour':
            rental_price *= 24
        product_data.update({
            'rental_price': rental_price,
            "category": product.category_id,
            "images": [i.image.url for i in product.images],
            "lon": product.point[0],
            "lat": product.point[1],
            'rental_unit': 'Day',
        })
        data.append(product_data)
    result = {
        'next_page': next_page,
        'products': data,
    }
    return CoastalJsonResponse(result)


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
            RecentlyViewed.objects.create(user=user, product=product)

    data = model_to_dict(product, fields=['category', 'id', 'for_rental', 'for_sale', 'sale_price', 'city', 'currency'])
    data['max_guests'] = product.max_guests or 0

    if product.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT):
        data['room'] = product.rooms or 0
        data['bathrooms'] = product.bathrooms or 0
    if product.category_id in (defs.CATEGORY_ROOM, defs.CATEGORY_YACHT):
        data['beds'] = product.beds or 0
        data['bathrooms'] = product.bathrooms or 0

    if product.point:
        data['lon'] = product.point[0]
        data['lat'] = product.point[1]
    if product.get_amenities_display():
        data['amenities'] = product.get_amenities_display()
    data['short_desc'] = product.short_desc
    if product.get_rental_unit_display():
        data['rental_unit'] = product.get_rental_unit_display()
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
    images = []
    views = []
    for pi in ProductImage.objects.filter(product=product):
        if pi.caption != ProductImage.CAPTION_360:
            images.append(pi.image.url)
        else:
            views.append(pi.image.url)

    data['360_images'] = views
    data['images'] = images
    if product.name:
        data['name'] = product.name
    else:
        data['name'] = 'Your Listing Name'
    if product.owner.userprofile.photo:
        photo = product.owner.userprofile.photo.url
    else:
        photo = ""
    data['owner'] = {
        'user_id': product.owner_id,
        'name': product.owner.get_full_name() or product.owner.email,
        'photo': photo,
    }
    data['reviews'] = {
        "count": 0,
        "avg_score": 0,
        # "latest_review": {
        #     "reviewer_name": "Sandra Ravikal",
        #     "reviewer_photo": "http://54.169.88.72/media/user/photo012.jpg",
        #     "stayed_range": "02/27 - 02/28",
        #     "score": 5,
        #     "content": "This is a sample rating of this listing."
        # }
    }
    price = get_product_discount(product.rental_price, product.rental_unit, product.discount_weekly, product.discount_monthly)
    data['extra_info'] = {
        'rules': {
            'name': '%s Rules' % product.category.name,
            'content': product.rental_rule or 'Nothing is set',
        },
        'cancel_policy': {
            'name': 'Cancellation Policy',
            'content': 'Coastal does not provide online cancellation service. Please contact us if you have any needs.'
        },
        'discount': {
            'name': 'Additional Price',
            'weekly_discount': product.discount_weekly or 0,
            'updated_weekly_price': price[0],
            'monthly_discount': product.discount_monthly or 0,
            'update_weekly_price': price[1],
        },
    }

    if product.for_sale == 1 and product.for_rental == 0:
        data.get('extra_info').pop('discount')

    similar_products = get_similar_products(product)
    bind_product_image(similar_products)
    similar_product_dict = []
    for p in similar_products:
        content = model_to_dict(p, fields=['id', 'category', 'liked', 'for_rental', 'for_sale', 'rental_price',
                                           'sale_price', 'city', 'max_guests'])
        content['reviews_count'] = 0
        content['reviews_avg_score'] = 0
        content['liked'] = p.id in liked_product_id_list
        content['image'] = ""
        for img in p.images:
            if img.caption != ProductImage.CAPTION_360:
                content['image'] = img.image.url
                break

        similar_product_dict.append(content)
    data['similar_products'] = similar_product_dict
    return CoastalJsonResponse(data)


@login_required
def product_image_upload(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    data = request.POST.copy()
    if 'product_id' in data:
        data['product'] = data.get('product_id')
    form = ImageUploadForm(data, request.FILES)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    image = form.save()
    data = {
        'image_id': image.id,
        'url': image.image.url,
    }
    return CoastalJsonResponse(data)


@login_required
def product_add(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    form = ProductAddForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    product = form.save(commit=False)
    product.owner = request.user

    product.save()
    pid = product.id
    black_out_date(pid, form)
    amenities = form.cleaned_data.get('amenities')
    for a in amenities:
        product.amenities.add(a)

    images = form.cleaned_data.get('images')
    for i in images:
        i.product = product
        i.save()

    data = {
        'product_id': product.id
    }
    return CoastalJsonResponse(data)


def calc_total_price(request):
    form = RentalDateForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)
    start_datetime = form.cleaned_data['start_datetime']
    end_datetime = form.cleaned_data['end_datetime']
    product_id = request.GET.get('product_id')
    product = Product.objects.filter(id=product_id)
    if not product:
        return CoastalJsonResponse(form.errors, status=404)
    rental_amount = calc_price(product[0], start_datetime, end_datetime)
    currency = product[0].currency
    symbol = Currency.objects.get(code=currency).symbol

    data = [{
        'amount': rental_amount[1],
        'currency': currency,
        'symbol': symbol,
    }]
    return CoastalJsonResponse(data)


def calc_price(product, start_date, end_date):
    rental_unit = product.rental_unit
    rental_price = product.rental_price
    total_time = end_date.timestamp() - start_date.timestamp()
    if rental_unit == 'day':
        rental_date = math.ceil(total_time / (24.0 * 3600.0))
    elif rental_unit == 'half-day':
        rental_date = math.ceil(total_time / (6.0 * 3600.0))
    else:
        rental_date = math.ceil(total_time / 3600.0)

    sub_rental_amount = math.ceil(rental_date * rental_price)

    if product.discount_monthly and total_time >= 30 * 24 * 3600:
        rental_amount = math.ceil(sub_rental_amount * (1 - product.discount_monthly / 100.0))
    elif product.discount_weekly and total_time >= 7 * 24 * 3600:
        rental_amount = math.ceil(sub_rental_amount * (1 - product.discount_weekly / 100.0))
    else:
        rental_amount = sub_rental_amount
    if rental_amount <= 0:
        rental_amount = 0
    return [sub_rental_amount, rental_amount]


@login_required
def product_update(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        product = Product.objects.get(id=request.POST.get('product_id'))
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)

    form = ProductUpdateForm(request.POST, instance=product)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    black_out_date(request.POST.get('product_id'), form)
    if 'amenities' in form.cleaned_data:
        for a in form.cleaned_data.get('amenities'):
            product.amenities.add(a)

    if 'images' in form.cleaned_data:
        for i in form.cleaned_data.get('images'):
            i.product = product
            i.save()
    product.save()

    if form.cleaned_data.get('action') == 'publish':
        if product.validate_publish_data():
            product.publish()
            product.save()
        else:
            return CoastalJsonResponse({'action': 'There are invalid data for publish.'}, status=response.STATUS_400)

    return CoastalJsonResponse()


def amenity_list(request):
    amenities = Amenity.objects.values_list('id', 'name', 'amenity_type')

    group_dict = {}
    for aid, name, amenity_type in amenities:
        if amenity_type not in group_dict:
            group_dict[amenity_type] = []
        group_dict[amenity_type].append({
            'id': aid,
            'name': name,
        })

    result = []
    amenity_type_dict = dict(Amenity.TYPE_CHOICES)
    for group, items in group_dict.items():
        result.append({
            'group': amenity_type_dict[group],
            'items': items
        })

    return CoastalJsonResponse(result)


@login_required
def toggle_favorite(request, pid):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    user = request.user
    favorite_item = FavoriteItem.objects.filter(favorite__user=user, product_id=pid)
    if not favorite_item:
        favorite, _ = Favorites.objects.get_or_create(user=user)
        FavoriteItem.objects.create(product_id=pid, favorite=favorite)
        data = {
            'product_id': pid,
            'is_liked': True,
        }
    else:
        favorite_item.delete()
        data = {
            'product_id': pid,
            'is_liked': False,
        }
    return CoastalJsonResponse(data)


def currency_list(request):
    currencies = Currency.objects.values('code', 'symbol')
    data = []
    for currency in currencies:
        data.append(currency)
    return CoastalJsonResponse(data)


def black_out_date(pid, form):
    date_list = form.cleaned_data.get('black_out_dates')
    if date_list:
        BlackOutDate.objects.all().delete()
        for black_date in date_list:
            BlackOutDate.objects.create(product_id=pid, start_date=black_date[0], end_date=black_date[1])


def recommend_product_list(request):
    recommend_products = Product.objects.filter(status='published').order_by('-score')[0:20]
    page = request.GET.get('page', 1)
    bind_product_image(recommend_products)
    data = []
    item = settings.PER_PAGE_ITEM
    paginator = Paginator(recommend_products, item)
    try:
        recommend_products = paginator.page(page)
    except PageNotAnInteger:
        recommend_products = paginator.page(1)
    except EmptyPage:
        recommend_products = paginator.page(paginator.num_pages)

    if int(page) >= paginator.num_pages:
        next_page = 0
    else:
        next_page = int(page) + 1
    for product in recommend_products:
        product_data = model_to_dict(product, fields=['id', 'for_rental', 'for_sale', 'rental_price', 'sale_price',
                                                      'beds', 'max_guests'])
        product_data.update({
            'category': product.category_id,
            'rental_unit': product.get_rental_unit_display(),
        })
        if product.images:
            product_data['images'] = [i.image.url for i in product.images]
        else:
            product_data['images'] = []
        if product.point:
            product_data.update({
                'lon': product.point[0],
                'lat': product.point[1],
            })
        data.append(product_data)
    result = {
        'recommend_products': data,
        'next_page': next_page
    }
    return CoastalJsonResponse(result)


@login_required
def discount_calculator(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)
    form = DiscountCalculatorFrom(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    rental_price = form.cleaned_data['rental_price']
    rental_unit = form.cleaned_data['rental_unit']
    discount_weekly = form.cleaned_data.get('discount_weekly')
    discount_monthly = form.cleaned_data.get('discount_monthly')

    price = get_product_discount(rental_price, rental_unit, discount_weekly, discount_monthly)

    data = {
        'weekly_price': price[0],
        'monthly_price': price[1],
    }
    return CoastalJsonResponse(data)


def delete_image(request):
    images = request.POST.get('images').split(',')
    for image in images:
        image = ProductImage.objects.filter(id=image)
        image.delete()
    return CoastalJsonResponse(message='OK')


def black_dates_for_rental(request):
    product_id = request.GET.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
    except:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")
    black_date_for_rental = product.blackoutdate_set.all()
    data = []
    for date in black_date_for_rental:
        date_data = [date.start_date, date.end_date]
        data.append(date_data)
    rental_order = RentalOrder.objects.filter(product=product)
    for date in rental_order:
        date_data = [date.start_datetime.date(), date.end_datetime.date()]
        data.append(date_data)
    return CoastalJsonResponse(data)


def search(request):
    products = Product.objects.filter(address__contains=request.GET.get('q')).order_by('-score', '-rental_usd_price', '-sale_price')
    bind_product_image(products)
    page = request.GET.get('page', 1)
    item = settings.PER_PAGE_ITEM
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
    liked_product_id_list = []
    if request.user.is_authenticated:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list('product_id',
                                                                                                     flat=True)
    products_list = []
    for product in products:
        data = {
            'type': product.category.name or '',
            'address': product.address or '',
            'reviews':  0,
            'rental_price': product.rental_price or 0,
            'sale_price': product.sale_price or 0,
            'beds': product.beds or 0,
            'length': product.length or 0,
            'city': product.city or '',
            'id': product.id,
            'category': product.category_id,
            'liked': product.id in liked_product_id_list,
            'for_rental': product.for_rental or '',
            'for_sale': product.for_sale or '',
            'max_guests': product.max_guests or 0,
            'rental_unit': product.get_rental_unit_display(),
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
