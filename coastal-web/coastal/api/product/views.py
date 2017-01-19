from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Avg, Count
from django.forms.models import model_to_dict
from django.views.decorators.cache import cache_page
from django.utils.timezone import localtime
from timezonefinder import TimezoneFinder
from datetime import datetime

from coastal.api import defines as defs
from coastal.api.product.forms import ImageUploadForm, ProductAddForm, ProductUpdateForm, ProductListFilterForm, \
    DiscountCalculatorFrom
from coastal.api.product.utils import get_similar_products, bind_product_image, count_product_view, \
    get_product_discount, calc_price, format_date
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.api.rental.forms import RentalBookForm

from coastal.apps.account.models import FavoriteItem, Favorites, RecentlyViewed
from coastal.apps.currency.models import Currency
from coastal.apps.currency.utils import price_display
from coastal.apps.product import defines as product_defs
from coastal.apps.product.models import Product, ProductImage, Amenity
from coastal.apps.rental.models import BlackOutDate, RentalOrder, RentalOutDate
from coastal.apps.review.models import Review
from coastal.apps.support.models import Report
from coastal.apps.coastline.utils import distance_from_coastline


def product_list(request):
    form = ProductListFilterForm(request.GET)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)

    lon = form.cleaned_data['lon']
    lat = form.cleaned_data['lat']
    distance = form.cleaned_data['distance'] or defs.DISTANCE

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
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)), status='published')

    if guests:
        products = products.filter(max_guests__gte=guests)
    if for_sale and for_rental:
        products = products.filter(for_rental=True) | products.filter(for_sale=True)
    elif for_rental:
        products = products.filter(for_rental=True)
    elif for_sale:
        products = products.filter(for_sale=True)
    if category:
        products = products.filter(category_id__in=category)
    if min_price:
        products = products.filter(rental_price__gte=min_price)
    if max_price:
        products = products.filter(rental_price__lte=max_price)
    if arrival_date:
        products = products.exclude(blackoutdate__start_date__lte=arrival_date,
                                    blackoutdate__end_date__gte=arrival_date).exclude(
            rentalorder__start_datetime__lte=arrival_date, rentalorder__end_datetime__gte=arrival_date)
    if checkout_date:
        products = products.exclude(blackoutdate__start_date__lte=checkout_date,
                                    blackoutdate__end_date__gte=checkout_date).exclude(
            rentalorder__start_datetime__lte=checkout_date, rentalorder__end_datetime__gte=checkout_date)
    if sort:
        products = products.order_by(sort.replace('price', 'rental_price'))
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
        if product.category_id == product_defs.CATEGORY_BOAT_SLIP:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'length',
                                                 'max_guests'])
            if not product.length:
                product_data['length'] = 0
        else:
            product_data = model_to_dict(product,
                                         fields=['id', 'for_rental', 'for_sale', 'beds',
                                                 'max_guests'])
        if product.for_rental:
            product_data.update({
                'rental_price': product.rental_price,
                'rental_unit': 'Day',
                'rental_price_display': product.get_rental_price_display(),
        })
            rental_price = product.rental_price
            if product.rental_unit == "half-day":
                rental_price *= 4
            if product.rental_unit == 'hour':
                rental_price *= 24
        if product.for_sale:
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
    data['rental_price_display'] = product.get_rental_price_display()
    data['sale_price_display'] = product.get_sale_price_display()
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
    if product.owner.userprofile.photo:
        photo = product.owner.userprofile.photo.url
    else:
        photo = ""
    data['owner'] = {
        'user_id': product.owner_id,
        'name': product.owner.get_full_name() or product.owner.email,
        'photo': photo,
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
            "reviewer_id": last_review.owner_id,
            "reviewer_name": last_review.owner.get_full_name(),
            "reviewer_photo": last_review.owner.userprofile.photo.url or '',
            "stayed_range": '%s - %s' % (datetime.strftime(start_time, '%Y/%m/%d'), datetime.strftime(end_time, '%Y/%m/%d')),
            "score": last_review.score,
            "content": last_review.content
        }
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

    if product.for_rental:
        price = get_product_discount(product.rental_price, product.rental_unit, product.discount_weekly, product.discount_monthly)
        discount = {
            'discount': {
                'name': 'Additional Price',
                'weekly_discount': product.discount_weekly or 0,
                'updated_weekly_price': price[0],
                'monthly_discount': product.discount_monthly or 0,
                'updated_monthly_price': price[1],
            }
        }
    else:
        discount = {
            'discount': {}
        }
    data.get('extra_info').update(discount)

    similar_products = get_similar_products(product)
    bind_product_image(similar_products)
    similar_product_dict = []
    for p in similar_products:
        content = model_to_dict(p, fields=['id', 'category', 'liked', 'for_rental', 'for_sale', 'rental_price',
                                           'sale_price', 'city', 'max_guests'])
        content['reviews_count'] = 0
        content['reviews_avg_score'] = 0
        content['liked'] = p.id in liked_product_id_list
        content['max_guests'] = p.max_guests or 0
        content['length'] = p.length or 0
        content['rooms'] = p.rooms or 0
        content['image'] = ""
        content['rental_price_display'] = p.get_rental_price_display()
        content['sale_price_display'] = p.get_sale_price_display()
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

    if 'lon' and 'lat' in form.data:
        tf = TimezoneFinder()
        product.timezone = tf.timezone_at(lng=form.cleaned_data['lon'], lat=form.cleaned_data['lat'])
        product.distance_from_coastal = distance_from_coastline(form.cleaned_data['lon'], form.cleaned_data['lat']) or float('inf')
    product.save()
    pid = product.id
    black_out_date(pid, form)
    amenities = form.cleaned_data.get('amenities')
    for a in amenities:
        product.amenities.add(a)

    # TODO: remove the 'images' and remove images from ProductAddForm
    images = form.cleaned_data.get('images')
    for i in images:
        i.product = product
        i.save()

    data = {
        'product_id': product.id
    }
    return CoastalJsonResponse(data)


def calc_total_price(request):
    data = request.GET.copy()
    if 'product_id' in data:
        data['product'] = data.get('product_id')
    form = RentalBookForm(data)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)

    start_datetime = form.cleaned_data['start_datetime']
    end_datetime = form.cleaned_data['end_datetime']
    rental_unit = form.cleaned_data['rental_unit']
    product = form.cleaned_data['product']

    total_amount = calc_price(product, rental_unit, start_datetime, end_datetime)[1]
    data = [{
        'amount': total_amount,
        'currency': product.currency,
        'amount_display': price_display(total_amount, product.currency),
    }]
    return CoastalJsonResponse(data)


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

    if 'lan' and 'lat' in form.cleaned_data:
        product.distance_from_coastal = distance_from_coastline(form.cleaned_data['lon'], form.cleaned_data['lat']) or float('inf')
    product.save()

    if form.cleaned_data.get('action') == 'cancel':
        product.status = 'cancelled'
        product.save()

    if form.cleaned_data.get('action') == 'publish':
        if product.validate_publish_data():
            product.publish()
            product.save()
        else:
            return CoastalJsonResponse({'action': 'There are invalid data for publish.'}, status=response.STATUS_400)

    return CoastalJsonResponse()


@cache_page(15 * 60)
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


@cache_page(15 * 60)
def currency_list(request):
    currencies = Currency.objects.values('code', 'symbol')
    data = []
    for currency in currencies:
        data.append(currency)
    return CoastalJsonResponse(data)


def black_out_date(pid, form):
    date_list = form.cleaned_data.get('black_out_dates')
    if date_list:
        BlackOutDate.objects.filter(product_id=pid).delete()
        for black_date in date_list:
            BlackOutDate.objects.create(product_id=pid, start_date=black_date[0], end_date=black_date[1])


def recommend_product_list(request):
    recommend_products = Product.objects.filter(status='published').order_by('-score')[0:20]
    page = request.GET.get('page', 1)
    bind_product_image(recommend_products)
    data = []
    item = defs.PER_PAGE_ITEM
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
        product_data = model_to_dict(product, fields=['id', 'for_rental', 'for_sale', 'rental_price', 'sale_price'])
        product_data.update({
            'beds': product.beds or 0,
            'max_guests': product.max_guests or 0,
            'length': product.length or 0,
            'category': product.category_id,
            'rental_unit': product.get_rental_unit_display(),
            'rental_price_display': product.get_rental_price_display(),
            'sale_price_display': product.get_sale_price_display(),
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
    from datetime import timedelta
    product_id = request.GET.get('product_id')
    rental_unit = request.GET.get('rental_unit')
    try:
        product = Product.objects.get(id=product_id)
    except:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")
    date_ranges = product.blackoutdate_set.all()
    data = []
    for dr in date_ranges:
        data.append([localtime(dr.start_date).date(), localtime(dr.end_date).date()])

    date_ranges2 = RentalOutDate.objects.filter(product=product)
    for dr in date_ranges2:
        start_date = localtime(dr.start_date)
        end_date = localtime(dr.end_date)
        if rental_unit == 'day':
            if product.category_id in (product_defs.CATEGORY_HOUSE, product_defs.CATEGORY_APARTMENT, product_defs.CATEGORY_ROOM):
                start_date = start_date - timedelta(hours=12)
                end_date = end_date - timedelta(hours=12) - timedelta(seconds=1)
                data.append([start_date.date(), end_date.date()])
            else:
                end_date = end_date - timedelta(seconds=1)
                data.append([start_date.date(), end_date.date()])
        else:
            if start_date.hour == 12:
                start_date += timedelta(hours=12)
            if end_date.hour == 12:
                end_date -= timedelta(hours=12)
            if start_date != end_date:
                end_date -= timedelta(seconds=1)
                data.append([start_date.date(), end_date.date()])

    return CoastalJsonResponse(data)


def search(request):
    products = Product.objects.filter(address__contains=request.GET.get('q'), status='published').order_by('-rank', '-score', '-rental_usd_price', '-sale_price')
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
        data = {
            'type': product.category.name or '',
            'address': product.address or '',
            'reviews':  product.review_set.all().count(),
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
            'rental_price_display': product.get_rental_price_display(),
            'sale_price_display': product.get_sale_price_display(),
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


def product_review(request):
    product_id = request.GET.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
    except RentalOrder.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)
    reviews = Review.objects.filter(product=product)
    user = product.owner
    owner = {
        'id': user.id,
        'name': user.get_full_name(),
        'photo': user.userprofile.photo and user.userprofile.photo.url or ''
    }
    product_dict = {
        'id': product_id,
        'name': product.name,
        'image': product.productimage_set.first() and product.productimage_set.first().image.url or ''
    }
    review_count = reviews.aggregate(Avg('score'), Count('id'))
    reviews_list = []
    if reviews:
        for review in reviews:
            review_dict = {
                'guest_id': review.owner_id,
                'guest_name': review.owner.get_full_name(),
                'guest_photo': review.owner.userprofile.photo and review.owner.userprofile.photo.url or '',
                'date': format_date(review.date_created) or '',
                'score': review.score,
                'content': review.content
            }
            reviews_list.append(review_dict)

    result = {
        'owner': owner,
        'product': product_dict,
        'review_count': review_count['id__count'],
        'reviews': reviews_list
    }
    return CoastalJsonResponse(result)


def product_owner(request):
    owner_id = request.GET.get('owner_id')
    try:
        user = User.objects.get(id=owner_id)
    except User.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)
    reviews = Review.objects.filter(order__owner=user).order_by('-date_created')
    review_avg_score = reviews.aggregate(Avg('score'), Count('id'))
    products = Product.objects.filter(owner=user, status='published')
    bind_product_image(products)
    spaces_list = []
    yachts_list = []
    jets_list = []
    for product in products:
        liked_product_id_list = []
        if request.user.is_authenticated:
            liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
                'product_id', flat=True)

        review = Review.objects.filter(product=product)
        reviews_avg_score = review.aggregate(Avg('score'), Count('id'))
        if product.category.get_root().id == 1:
            spaces_list.append({
                "id": product.id,
                "category": product.category_id,
                "image": product.images and product.images[0].image.url or '',
                "liked": product.id in liked_product_id_list,
                "for_rental": product.for_rental,
                "for_sale": product.for_sale,
                "rental_price": product.rental_price,
                "rental_price_display": product.get_rental_price_display(),
                "rental_unit": product.get_rental_unit_display(),
                "sale_price": product.sale_price,
                "sale_price_display": product.get_sale_price_display(),
                "city": product.city,
                "max_guests": product.max_guests or 0,
                'beds': product.beds or 0,
                'rooms': product.rooms or 0,
                "reviews_count": reviews_avg_score['id__count'],
                "reviews_avg_score": reviews_avg_score['score__avg'] or 0,
            })
        elif product.category.get_root().id == 2:
            yachts_dict ={
                "id": product.id,
                "category": product.category_id,
                "image": product.images and product.images[0].image.url or '',
                "liked": product.id in liked_product_id_list,
                "for_rental": product.for_rental,
                "for_sale": product.for_sale,
                "rental_price": product.rental_price,
                "rental_price_display": product.get_rental_price_display(),
                "rental_unit": product.get_rental_unit_display(),
                "sale_price": product.sale_price,
                "sale_price_display": product.get_sale_price_display(),
                "city": product.city,
                "max_guests": product.max_guests or 0,
                'rooms': product.rooms or 0,
                "reviews_count": reviews_avg_score['id__count'],
                "reviews_avg_score": reviews_avg_score['score__avg'] or 0
            }
            if product.category.id == product_defs.CATEGORY_BOAT_SLIP:
                yachts_dict['length'] = product.length or 0
            else:
                yachts_dict['beds'] = product.beds or 0
            yachts_list.append(yachts_dict)
        else:
            jets_list.append({
                "id": product.id,
                "category": product.category_id,
                "image": product.images and product.images[0].image.url or '',
                "liked": product.id in liked_product_id_list,
                "for_rental": product.for_rental,
                "for_sale": product.for_sale,
                "rental_price": product.rental_price,
                "rental_price_display": product.get_rental_price_display(),
                "rental_unit": product.get_rental_unit_display(),
                "sale_price": product.sale_price,
                "sale_price_display": product.get_sale_price_display(),
                "city": product.city,
                "max_guests": product.max_guests or 0,
                'beds': product.beds or 0,
                'rooms': product.rooms or 0,
                "reviews_count": reviews_avg_score['id__count'],
                "reviews_avg_score": reviews_avg_score['score__avg'] or 0,
            })

    owner = {
        'id': user.id,
        'name': user.get_full_name(),
        'email': user.email,
        'photo': user.userprofile.photo and user.userprofile.photo.url or ''
    }
    if reviews:
        latest_review = {
            'guest_id': reviews[0].owner_id,
            'guest_name': reviews[0].owner.get_full_name(),
            'guest_photo': reviews[0].owner.userprofile.photo and reviews[0].owner.userprofile.photo.url or '',
            'date': format_date(reviews[0].date_created),
            'score': reviews[0].score,
            'content': reviews[0].content
        }
    else:
        latest_review = {
        }

    products = {
        'spaces': spaces_list,
        'yachts': yachts_list,
        'jets': jets_list
    }
    result = {
        'owner': owner,
        'review_count': review_avg_score['id__count'],
        'review_avg_score': review_avg_score['score__avg'] or 0,
        'latest_review': latest_review,
        'products': products
    }
    return CoastalJsonResponse(result)


def product_owner_reviews(request):
    owner_id = request.GET.get('owner_id')
    try:
        user = User.objects.get(id=owner_id)
    except User.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)
    except ValueError:
        return CoastalJsonResponse(status=response.STATUS_404)
    reviews = Review.objects.filter(order__owner=user)
    review_avg_score = reviews.aggregate(Avg('score'), Count('id'))
    reviews_list = []
    for review in reviews:
        reviews_list.append({
            'guest_id': review.owner_id,
            'guest_name': review.owner.get_full_name(),
            'guest_photo': review.owner.userprofile.photo and review.owner.userprofile.photo.url or '',
            'date': format_date(review.date_created),
            'score': review.score,
            'content': review.content
        })
    owner = {
        'id': user.id,
        'name': user.get_full_name(),
        'photo': user.userprofile.photo and user.userprofile.photo.url or ''
    }

    result = {
        'owner': owner,
        'review_count': review_avg_score['id__count'],
        'reviews': reviews_list,
    }
    return CoastalJsonResponse(result)


@login_required
def flag_junk(request):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    product = Product.objects.get(id=request.POST.get('pid'))
    if request.POST.get('reported') == '1':
        Report.objects.create(product=product, user=request.user)
    return CoastalJsonResponse()
