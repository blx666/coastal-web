# coding:utf-8
from coastal.apps.product.models import Product, ProductImage, ProductViewCount
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import F


def get_similar_products(product):
    point = product.point

    if point:
        similar_distance_product = Product.objects.filter(point__distance_lte=(point, D(mi=35))).exclude(
            id=product.id).order_by(Distance('point', point))[0:12]
    else:
        similar_distance_product = Product.objects.all()[0:12]

    price = product.rental_price
    price_order = Product.objects.order_by('rental_price')
    product_index = list(price_order).index(product)
    if product_index >= 20:
        price_order_product = price_order[product_index - 20: product_index + 20]
    else:
        price_order_product = price_order[0:product_index + 20]
    similar_price_product = sorted(price_order_product,
                                   key=lambda price_order_product: abs(price_order_product.rental_price - price))
    similar_price_product = list(similar_price_product)
    similar_distance_product = list(similar_distance_product)
    similar_price_product.reverse()
    similar_price_product.remove(product)

    for similar_price in similar_price_product:
        if similar_price in similar_distance_product:
            similar_price_product.remove(similar_price)
    similar_product = similar_distance_product + similar_price_product
    similar_product = similar_product[0:20]
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
    product_images = ProductImage.objects.filter(product__in=products)

    image_group = {}
    for image in product_images:
        if image.product.id not in image_group:
            image_group[image.product.id] = []
        image_group[image.product.id].append(image)

    for product in products:
        product.images = image_group.get(product.id, [])


def count_product_view(product):
    try:
        product_view = ProductViewCount.objects.get(product=product)
        product_view.count = F('count') + 1
        product_view.save()
    except ProductViewCount.DoesNotExist:
        ProductViewCount.objects.create(product=product, count=1)

