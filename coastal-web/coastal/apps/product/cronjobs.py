from coastal.apps.account.models import FavoriteItem
from coastal.apps.product.models import Product, ProductViewCount
from coastal.apps.currency.models import Currency
import urllib.request
import json


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
                currency.save()

