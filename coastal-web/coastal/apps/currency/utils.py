from django.core.cache import cache
from coastal.apps.currency.models import Currency


def currencies():
    currency_dict = cache.get('currency_dict')
    if currency_dict is not None:
        return currency_dict

    currency_dict = {c['code']: c for c in Currency.objects.values('code', 'symbol', 'rate', 'display')}
    cache.set('currency_dict', currency_dict, 60 * 60)
    return currency_dict


def get_exchange_rate(currency):
    """
    :param currency: string e.g. "USD"
    :return: float
    """
    currency_info = currencies().get(currency.upper())
    if currency_info:
        return currency_info['rate']
    return 0.0


def price_display(price, currency):
    """
    display currency before price
    :param price: float
    :param currency: string e.g. "USD"
    :return: string e.g. "US$100"
    """
    currency_info = currencies().get(currency.upper())
    if price and currency_info:
        return '%s%s' % (currency_info['display'], format(int(price), ','))
    return ''
