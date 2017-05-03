from coastal.apps.account.models import FavoriteItem
from coastal.apps.product.models import Product, ProductViewCount
from coastal.apps.currency.models import Currency
from coastal.apps.currency.utils import get_exchange_rate
from coastal.apps.product import defines as defs
from coastal.api.page.views import get_home_banners, get_home_product_list
from django.core.cache import cache
from coastal.core import cache_defines as cache_keys
from coastal.api import defines as coastal_defs
from django.core.paginator import Paginator


from django.utils import timezone
import urllib.request
import json
import math


def update_product_score():
    products = Product.objects.all()
    for product in products:
        score = 0
        product_view_count = ProductViewCount.objects.filter(product=product).first()
        if product_view_count:
            score += product_view_count.count
        liked_count = FavoriteItem.objects.filter(product=product).count()
        product.score = score + 7 * liked_count
        product.save()


def exchange_rate():
    try:
        response = urllib.request.urlopen('http://api.fixer.io/latest?base=USD')
        rates = json.loads(response.read().decode('utf-8'))
    except:
        # TODO: add log
        return

    all_currency = Currency.objects.all()
    for currency in all_currency:
        if currency.code in rates['rates']:
            if currency.rate != rates['rates'][currency.code]:
                currency.rate = rates['rates'][currency.code]
                currency.update_rate_time = timezone.now()
                currency.save()

    products = Product.objects.all()
    for product in products:
        currency_rate = get_exchange_rate(product.currency)
        if product.rental_price and product.rental_unit:
            product.rental_usd_price = math.ceil(product.get_price('day') / currency_rate)
        if product.sale_price:
            product.sale_usd_price = math.ceil(product.sale_price / currency_rate)
        if product.rental_price and product.category_id == defs.CATEGORY_ADVENTURE:
            product.rental_usd_price = math.ceil(product.rental_price / currency_rate)
        product.save()


def update_cache():
    cache.delete(cache_keys.CACHE_HOME_BANNER_KEY)
    get_home_banners()
    for page in range(1, 11):
        cache.delete(cache_keys.CACHE_HOME_PRODUCT_LIST_KEY % page)
        get_home_product_list(page)