from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.forms.models import model_to_dict

from coastal.api.product.forms import ImageUploadForm, ProductAddForm, ProductUpdateForm, ProductListFilterForm, \
    DiscountCalculatorFrom, RentalDateForm
from coastal.api.product.utils import get_similar_products, bind_product_image, count_product_view
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core.decorators import login_required
from coastal.apps.product.models import Product, ProductImage, Amenity
from coastal.apps.account.models import FavoriteItem, Favorites, RecentlyViewed
from coastal.apps.currency.models import Currency
from coastal.apps.rental.models import BlackOutDate


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
    target = Point(lon, lat)
    products = Product.objects.filter(point__distance_lte=(target, D(mi=distance)))

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

    data = []
    for product in products[0:20]:
        product_data = model_to_dict(product,
                                     fields=['id', 'for_rental', 'for_sale', 'rental_unit', 'beds',
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
        })
        data.append(product_data)
    return CoastalJsonResponse(data)


def product_detail(request, pid):
    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404, message="The product does not exist.")

    user = request.user
    if user.is_authenticated():
        RecentlyViewed.objects.create(user=user, product=product)
    count_product_view(product)

    data = model_to_dict(product, fields=['category', 'id', 'for_rental', 'for_sale', 'rental_price', 'rental_unit',
                                          'sale_price', 'city', 'max_guests', 'max_guests', 'reviews_count',
                                          'reviews_avg_score'])
    if product.point:
        data['lon'] = product.point[0]
        data['lat'] = product.point[1]
    data['amenities'] = product.get_amenities_display()
    data['short_desc'] = product.short_desc

    liked_product_id_list = []
    if request.user.is_authenticated:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=request.user).values_list(
            'product_id', flat=True)

    data['liked'] = product.id in liked_product_id_list
    images = []
    for pi in ProductImage.objects.filter(product=product).exclude(caption=ProductImage.CAPTION_360):
        images.append(pi.image.url)

    data['images'] = images
    if product.owner.userprofile.photo:
        photo = product.owner.userprofile.photo.url
    else:
        photo = ""
    data['owner'] = {
        'user_id': product.owner_id,
        'name': product.owner.get_full_name(),
        'photo': photo,
    }
    data['reviews'] = {
        "count": 8,
        "avg_score": 4.3,
        "latest_review": {
            "reviewer_name": "Sandra Ravikal",
            "reviewer_photo": "http://54.169.88.72/media/user/photo012.jpg",
            "stayed_range": "02/27 - 02/28",
            "score": 5,
            "content": "This is a sample rating of this listing."
        }
    }
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


def get_rental_amount(request, pid):
    form = RentalDateForm(request.POST)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=400)
    arrival_date = form.cleaned_data['arrival_date']
    checkout_date = form.cleaned_data['checkout_date']
    product = Product.objects.filter(id=pid)
    if not product:
        return CoastalJsonResponse(form.errors, status=404)
    rental_price = product[0].rental_price
    rental_date = (checkout_date - arrival_date).seconds/3600/24 + (checkout_date - arrival_date).days
    rental_amount = rental_date * rental_price
    data = [{
        'total_amount': rental_amount,
        # 'rental_price': rental_price,
        # 'rental_date': rental_date,
        # 'a': arrival_date,
        # 'b': checkout_date,
    }]
    return CoastalJsonResponse(data)


@login_required
def product_update(request, pid):
    if request.method != 'POST':
        return CoastalJsonResponse(status=response.STATUS_405)

    try:
        product = Product.objects.get(id=pid)
    except Product.DoesNotExist:
        return CoastalJsonResponse(status=response.STATUS_404)

    form = ProductUpdateForm(request.POST, instance=product)
    if not form.is_valid():
        return CoastalJsonResponse(form.errors, status=response.STATUS_400)
    black_out_date(pid, form)
    if 'amenities' in form.cleaned_data:
        for a in form.cleaned_data.get('amenities'):
            product.amenities.add(a)

    if 'images' in form.cleaned_data:
        for i in form.cleaned_data.get('images'):
            i.product = product
            i.save()

    if form.cleaned_data.get('action') == 'published':
        if product.validate_publish_data():
            product.publish()
            product.save()
        else:
            return CoastalJsonResponse({'action': 'There are invalid data for publish.'}, status=response.STATUS_400)
    product.save()
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
    date_list = form.cleaned_data.get('black_out_days')
    if date_list:
        BlackOutDate.objects.all().delete()
        for black_date in date_list:
            BlackOutDate.objects.create(product_id=pid, start_date=black_date[0], end_date=black_date[1])


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
    weekly_price = 0
    monthly_price = 0
    if rental_unit == "half-day":
        rental_price *= 4
    if rental_unit == 'hour':
        rental_price *= 24
    if discount_weekly:
        weekly_price = int(rental_price * 7 * discount_weekly / 100)+1
    if discount_monthly:
        monthly_price = int(rental_price * 30 * discount_monthly / 100)+1

    data = {
            'weekly_price': weekly_price,
            'monthly_price': monthly_price,
        }
    return CoastalJsonResponse(data)
