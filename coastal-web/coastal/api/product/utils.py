# coding:utf-8
import math
import datetime
from coastal.apps.product.models import Product, ProductImage, ProductViewCount
from coastal.apps.rental.models import BlackOutDate, RentalOrder
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import F
from coastal.apps.product import defines as defs
from django.contrib.gis.geos import Point, Polygon
from coastal.apps.account.models import FavoriteItem


def get_similar_products(product):
    if product.point:
        similar_distance_product = Product.objects.filter(
            status='published', point__distance_lte=(product.point, D(mi=35))).exclude(id=product.id).order_by(
            Distance('point', product.point))[0:12]
    else:
        similar_distance_product = Product.objects.filter(
            status='published', country=product.country, administrative_area_level_1=product.administrative_area_level_1,
            locality=product.locality).exclude(id=product.id).order_by('-score')[0:12]

    if product.status == 'published' and (product.rental_price or product.sale_price):
        if product.rental_price:
            price = product.rental_price
            if similar_distance_product:
                price_order = Product.objects.filter(status='published', rental_price__gt=0).order_by('rental_usd_price').exclude(id__in=similar_distance_product.values_list('id', flat=True))
            else:
                price_order = Product.objects.filter(status='published', rental_price__gt=0).order_by('rental_usd_price')
            product_index = list(price_order).index(product)
            if product_index >= 8:
                price_order_product = price_order[product_index - 8: product_index + 8]
            else:
                price_order_product = price_order[0:product_index + 8]
            similar_price_product = sorted(price_order_product,
                                           key=lambda price_order_product: abs(price_order_product.rental_price - price))
        else:
            price = product.sale_price
            if similar_distance_product:
                price_order = Product.objects.filter(status='published', sale_price__gt=0).order_by('sale_usd_price').exclude(id__in=similar_distance_product.values_list('id', flat=True))
            else:
                price_order = Product.objects.filter(status='published', sale_price__gt=0).order_by('sale_usd_price')
            product_index = list(price_order).index(product)
            if product_index >= 8:
                price_order_product = price_order[product_index - 8: product_index + 8]
            else:
                price_order_product = price_order[0:product_index + 8]
            similar_price_product = sorted(price_order_product,
                                           key=lambda price_order_product: abs(price_order_product.sale_price - price))
        similar_price_product = list(similar_price_product)

        similar_price_product.reverse()
        similar_price_product.remove(product)
        similar_price_product = similar_price_product[0:8]
    else:
        similar_price_product = []

    similar_product = list(similar_distance_product) + similar_price_product
    pis = ProductImage.objects.filter(product__in=similar_product)
    for product in similar_product:
        product.images = []
        for pi in pis:
            if pi.product == product:
                product.images.append(pi)

    return similar_product


def bind_product_image(products):
    """
    It will bind images into product to avoid n+1 select.
    :param products: product obj list
    :return: None
    """
    product_images = ProductImage.objects.filter(product__in=products).exclude(image_type=ProductImage.CAPTION_360)

    image_group = {}
    for image in product_images:
        if image.product.id not in image_group:
            image_group[image.product.id] = []
        image_group[image.product.id].append(image)

    for product in products:
        product.images = image_group.get(product.id, [])


def bind_product_main_image(products):
    product_images = ProductImage.objects.filter(product__in=products).exclude(image_type=ProductImage.CAPTION_360)

    images = {}
    for image in product_images:
        if image.product.id not in images:
            images[image.product.id] = image

    for product in products:
        product.main_image = images.get(product.id)


def count_product_view(product):
    product_view = ProductViewCount.objects.filter(product=product).update(count=F('count') + 1)
    if not product_view:
        ProductViewCount.objects.create(product=product, count=1)


def get_product_discount(rental_price, rental_unit, discount_weekly=0, discount_monthly=0):
    updated_weekly_price = 0
    updated_monthly_price = 0
    if rental_unit == "half-day":
        rental_price *= 4
    if rental_unit == 'hour':
        rental_price *= 24
    if discount_weekly is not None:
        updated_weekly_price = math.ceil(rental_price * 7 * (1 - discount_weekly/100.0))
    if discount_monthly is not None:
        updated_monthly_price = math.ceil(rental_price * 30 * (1 - discount_monthly/100.0))

    data = [updated_weekly_price, updated_monthly_price]
    return data


def calc_price(product, rental_unit, start_date, end_date, guest_count):
    if product.category_id == defs.CATEGORY_ADVENTURE:
        rental_amount = math.ceil(product.rental_price * guest_count)
        return [rental_amount, rental_amount, False, False]
    else:
        rental_price = product.get_price(rental_unit)
        if product.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT, defs.CATEGORY_ROOM) and rental_unit == 'day':
            end_date -= datetime.timedelta(days=1)

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
            discount_type = 'm'
            discount_rate = product.discount_monthly
        elif product.discount_weekly and total_time >= 7 * 24 * 3600:
            rental_amount = math.ceil(sub_rental_amount * (1 - product.discount_weekly / 100.0))
            discount_type = 'w'
            discount_rate = product.discount_weekly
        else:
            rental_amount = sub_rental_amount
            discount_rate = False
            discount_type = False
        if rental_amount <= 0:
            rental_amount = 0
        return [sub_rental_amount, rental_amount, discount_type, discount_rate]


def format_date(value, default=None):
    if value:
        return value.strftime('%m/%d/%Y')
    else:
        return default


def get_products_by_id(product_ids):
    products = Product.objects.filter(id__in=product_ids)
    bind_product_main_image(products)
    return {p.id: p for p in products}


def get_email_cipher(email):
    email_owner_list = email.split('@')
    email_cipher = '%s***@%s' % (email_owner_list[0][0:3], email_owner_list[1])

    return email_cipher


def set_point(northeast_lon, northeast_lat, southwest_lon, southwest_lat):
    first_point = Point(northeast_lon, northeast_lat)
    second_point = Point(northeast_lon, southwest_lat)
    third_point = Point(southwest_lon, southwest_lat)
    fourth_point = Point(southwest_lon, northeast_lat)
    poly = Polygon((first_point, second_point, third_point, fourth_point, first_point),)
    return poly


def bind_products_liked(products, logging, user):
    liked_dict = {}
    if user and logging:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=user).values_list(
                'product_id', flat=True)
        for product in products:
            liked_dict[product.id] = product.id in liked_product_id_list
    else:
        for product in products:
            liked_dict[product.id] = False
    return liked_dict


def bind_product_liked(product, logging, user):
    if user and logging:
        liked_product_id_list = FavoriteItem.objects.filter(favorite__user=user).values_list(
                'product_id', flat=True)
        return product.id in liked_product_id_list
    else:
        return False
