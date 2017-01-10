from coastal.apps.currency.models import Currency


def currency_list():
    currencies = Currency.objects.values()
    return {c['code']: c for c in currencies}
