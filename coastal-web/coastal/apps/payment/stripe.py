import math
import stripe
import logging
from django.conf import settings
from coastal.apps.rental.models import PaymentEvent
from coastal.apps.sale.models import SalePaymentEvent

logger = logging.getLogger(__name__)

# TODO update api_key
if settings.DEBUG:
    stripe.api_key = 'sk_test_ukQxxa9ekp1PMxszgUuK3jep'
else:
    stripe.api_key = 'sk_live_pIV7YwtljsRrloOU7zenFn5n'


def add_card(user, token):
    if user.userprofile.stripe_customer_id:
        customer = stripe.Customer.retrieve(user.userprofile.stripe_customer_id)
        customer.sources.create(card=token)
    else:
        customer = stripe.Customer.create(
            source=token,
            email=user.email,
            description="from Coastal APP",
        )
        user.userprofile.stripe_customer_id = customer.stripe_id
        user.userprofile.save()


def get_stripe_info(user):
    if user.userprofile.stripe_customer_id:
        customer = stripe.Customer.retrieve(user.userprofile.stripe_customer_id)
        info = {
            "has_more": customer.sources.has_more,
            "total_count": customer.sources.total_count,
            "id": customer.id,
            "default_source": customer.default_source,
            "sources": {"data": []}
        }

        for card in customer.sources.data:
            info['sources']['data'].append({
                "brand": card.brand,
                "customer": card.customer,
                "cvc_check": card.cvc_check,
                "exp_month": card.exp_month,
                "exp_year": card.exp_year,
                "id": card.id,
                "last4": card.last4,
                "funding": card.funding
            })
        return info
    return {}


def get_card_list(user):
    card_list = []

    if user.userprofile.stripe_customer_id:
        customer = stripe.Customer.retrieve(user.userprofile.stripe_customer_id)
        default_card = customer.default_source
        for i in customer.sources:
            card_list.append({
                "id": i.stripe_id,
                "last4": i.last4,
                "brand": i.brand,
                "is_default": i.stripe_id == default_card,
            })

    return card_list


def get_stripe_amount(amount, currency='USD'):
    """
    add stripe fee into amount, refer to https://support.stripe.com/questions/can-i-charge-my-stripe-fees-to-my-customers
    :param amount: float
    :param currency:
    :return: float
    """
    # TODO
    fixed = 0.3
    percent = 0.029
    return math.ceil((amount + fixed) / (1 - percent))


def charge(rental_order, user, card):
    if not user.userprofile.stripe_customer_id:
        return False

    stripe_amount = get_stripe_amount(rental_order.total_price, rental_order.currency)

    _charge = stripe.Charge.create(
        amount=stripe_amount * 100,  # Amount in cents
        currency=rental_order.currency.lower(),
        customer=user.userprofile.stripe_customer_id,
        card=card,
        metadata={"order_id": rental_order.number},
    )
    logger.debug('Stripe Charge: \n%s' % charge)

    if not _charge.paid:
        return False

    PaymentEvent.objects.create(
        order=rental_order,
        payment_type='stripe',
        amount=rental_order.total_price,
        stripe_amount=stripe_amount,
        currency=rental_order.currency,
        reference=_charge.id
    )

    try:
        transaction = stripe.Balance.retrieve(id=_charge.balance_transaction)
        coastal_dollar = transaction.net
    except TypeError as e:
        logger.error('Get Stripe Balance Error: \n%s' % e)
        coastal_dollar = rental_order.total_price_usd

    rental_order.coastal_dollar = math.floor(coastal_dollar)
    rental_order.save()

    return True


def sale_charge(sale_order, user, card):
    if not user.userprofile.stripe_customer_id:
        return False

    stripe_amount = get_stripe_amount(sale_order.price, sale_order.currency)

    _charge = stripe.Charge.create(
        amount=stripe_amount * 100,  # Amount in cents
        currency=sale_order.currency.lower(),
        customer=user.userprofile.stripe_customer_id,
        card=card,
        metadata={"order_id": sale_order.number},
    )
    if not _charge.paid:
        return False

    SalePaymentEvent.objects.create(
        sale_offer=sale_order,
        payment_type='stripe',
        amount=sale_order.price,
        stripe_amount=stripe_amount,
        currency=sale_order.currency,
        reference=_charge.id
    )

    try:
        transaction = stripe.Balance.retrieve(id=_charge.balance_transaction)
        coastal_dollar = transaction.net
    except TypeError as e:
        logger.error('Get Stripe Balance Error: \n%s' % e)
        coastal_dollar = sale_order.price_usd

    sale_order.coastal_dollar = math.floor(coastal_dollar)
    sale_order.status = 'pay'
    sale_order.save()

    return True


# charge = stripe.Charge.create(
#     amount=1000,  # Amount in cents
#     currency="usd",
#     source='tok_19UiVAIwZ8ZTWo9bF8Z6L6Ua',  # token
#     description="test charge by yijun"
# )
#
#
# customer = stripe.Customer.create(
#   source='tok_19Ui7ZIwZ8ZTWo9bzRf7807t',  # token
#   description="Test User 001"
# )
#
# stripe.Charge.create(
#   amount=2000,  # in cents
#   currency="cny",
#   customer='cus_9oKnNn8RLvpcGJ',
#   metadata={"order_id": "6735"},
# )
#
#
# customer = stripe.Customer.retrieve('cus_9oKnNn8RLvpcGJ')
# customer.sources.create(card='tok_19UiVAIwZ8ZTWo9bF8Z6L6Ua')
#
# stripe.Charge.create(
#   amount=100,  # in cents
#   currency="usd",
#   customer='cus_9oKnNn8RLvpcGJ',
#   card = 'card_19UiVAIwZ8ZTWo9bYTC4hguE',
#   metadata={"order_id": "6735"},
# )
