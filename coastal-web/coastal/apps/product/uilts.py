# coding:utf-8
from coastal.apps.product.models import Product, ProductImage
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import F
from django.db.models.functions import Greatest


def similar_products(product):
    similar_product = []
    point = product.point
    similar_product_dict = []
    similar_distance_product = Product.objects.filter(point__distance_lte=(point, D(km=10000))).order_by(
        Distance('point', point))[0:8]
    price = product.rental_price
    delta_expr = Greatest(F('rental_price') - price, price - F('rental_price'))
    similar_price_product = Product.objects.order_by(delta_expr)[0:13]
    similar_price_product = list(similar_price_product)
    for similar_price_02 in similar_price_product:
        if similar_price_02 in similar_distance_product:
            similar_price_product.remove(similar_price_02)
    similar_product += similar_distance_product
    similar_product += similar_price_product
    similar_product.remove(product)

    for p in similar_product[0:12]:
        images = ProductImage.objects.filter(product=p)
        image = [product_image.image.url for product_image in images]
        content = {
            'id': p.id,
            'category': p.category.id,
            'image': image,
            'liked': False,
            'for_rental': p.for_rental,
            'for_sale': p.for_sale,
            'rental_price': p.rental_price,
            'rental_unit': p.rental_unit,
            'sale_price': None,
            'city': p.city,
            'max_guests': p.max_guests,
            # 'speed': p.speed,
            'reviews_count': 0,
            'reviews_avg_score': 0,
        }
        similar_product_dict.append(content)
    return similar_product_dict
