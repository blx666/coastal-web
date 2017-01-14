from coastal.apps.account.models import Transaction
from coastal.apps.rental.models import PaymentEvent


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

    rental_order.coastal_dollar = rental_order.total_price_usd
    rental_order.status = 'booked'
    rental_order.save()

    return True
