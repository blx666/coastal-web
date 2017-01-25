from coastal.apps.payment.stripe import get_stripe_amount, get_card_list
from coastal.apps.currency.utils import price_display


def get_payment_info(rental_order, user):
    payment_info = {}

    if rental_order.total_price_usd < user.coastalbucket.balance:
        payment_info['payment_list'] = ['coastal', 'stripe']
        payment_info['coastal'] = {
            'coastal_dollar': user.coastalbucket.balance,
            'amount': rental_order.total_price_usd,
        }
    else:
        payment_info['payment_list'] = ['stripe']

    stripe_amount = get_stripe_amount(rental_order.total_price)  # add the stripe process fee
    payment_info['stripe'] = {
        'updated_amount': stripe_amount,
        'updated_amount_display': price_display(stripe_amount, rental_order.product.currency),
    }

    return payment_info


def sale_payment_info(saleoffer, user):
    payment_info = {}
    payment_info['payment_list'] = ['coastal', 'stripe']
    payment_info['coastal'] = {
        'coastal_dollar': user.coastalbucket.balance,
        'amount': saleoffer.price,
    }

    stripe_amount = get_stripe_amount(saleoffer.price)
    payment_info['stripe'] = {
        'updated_amount': stripe_amount,
        'updated_amount_display': price_display(stripe_amount, saleoffer.product.currency),
        'cards': get_card_list(user),
    }
    return payment_info