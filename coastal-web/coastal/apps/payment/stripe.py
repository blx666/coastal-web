import stripe
from django.conf import settings

if settings.DEBUG:
    stripe.api_key = 'sk_test_G1qgKMtou6ZrZc5eKOiMroCa'
else:
    stripe.api_key = 'sk_test_G1qgKMtou6ZrZc5eKOiMroCa'


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
        user.save()


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


def get_strip_payment_info(amount, currency):
    # TODO: update the calculate with https://support.stripe.com/questions/can-i-charge-my-stripe-fees-to-my-customers
    return {
        'updated_amount': amount,
        'currency': currency,
        'updated_amount_display': 'US$%s' % int(amount),
    }


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
#   amount=100,  # in cents
#   currency="usd",
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
