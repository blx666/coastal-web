from coastal.apps.account.models import Transaction
from coastal.apps.rental.models import PaymentEvent
from coastal.apps.sale.models import SalePaymentEvent


def charge(rental_order, user):
    if user.coastalbucket.balance < rental_order.total_price_usd:
        return False

    Transaction.objects.create(
        bucket=user.coastalbucket,
        type='out',
        order_number=rental_order.number
    )

    user.coastalbucket.balance -= rental_order.total_price_usd
    user.coastalbucket.save()

    PaymentEvent.objects.create(
        order=rental_order,
        payment_type='coastal',
        amount=rental_order.total_price_usd,
        currency='USD',
    )

    return True


def sale_charge(sale_order, user):
    if user.coastalbucket.balance < sale_order.price_usd:
        return False

    Transaction.objects.create(
        bucket=user.coastalbucket,
        type='out',
        order_number=sale_order.number
    )

    user.coastalbucket.balance -= rental_order.price_usd
    user.coastalbucket.save()

    SalePaymentEvent.objects.create(
        order=sale_order,
        payment_type='coastal',
        amount=sale_order.price_usd,
        currency='USD',
    )

    sale_order.coastal_dollar = sale_order.price_usd
    sale_order.status = 'pay'
    sale_order.save()

    return True
