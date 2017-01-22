from coastal.apps.account.models import FavoriteItem
from coastal.apps.product.models import Product, ProductViewCount
from coastal.apps.currency.models import Currency
from coastal.apps.rental.models import RentalOrder
from coastal.apps.sale.models import SaleOffer
from coastal.apps.currency.utils import get_exchange_rate

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
        return
    all_currency = Currency.objects.all()
    for currency in all_currency:
        if currency.code in rates['rates']:
            if currency.rate != rates['rates'][currency.code]:
                currency.rate = rates['rates'][currency.code]
                currency.update_rate_time = timezone.now()
                currency.save()

    rental_orders = RentalOrder.objects.all()
    for rental_order in rental_orders:
        rental_order.currency_rate = get_exchange_rate(rental_order.currency)
        rental_order.total_price_usd = math.ceil(rental_order.total_price / rental_order.currency_rate)
        rental_order.save()
    sale_offers = SaleOffer.objecys.all()
    for sale_offer in sale_offers:
        sale_offer.currency_rate = get_exchange_rate(sale_offer.currency)
        sale_offer.price_usd = math.ceil(sale_offer.price / sale_offer.currency_rate)
        sale_offer.save()