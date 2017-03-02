from coastal.apps.payment.stripe import get_stripe_amount, get_card_list
from coastal.apps.currency.utils import price_display


def get_payment_info(rental_order, user):
    payment_info = {}

    if rental_order.total_price_usd < user.coastalbucket.balance:
        payment_info['payment_list'] = ['coastal', 'stripe']
        payment_info['coastal'] = {
            'coastal_dollar': '$%s' % format(int(user.coastalbucket.balance), ','),
            'amount': '$%s' % format(int(rental_order.total_price_usd), ','),
        }
    else:
        payment_info['payment_list'] = ['stripe']

    stripe_amount = get_stripe_amount(rental_order.total_price)  # add the stripe process fee
    payment_info['stripe'] = {
        'total_price': rental_order.total_price,
        'total_price_display': rental_order.get_total_price_display(),
        'updated_amount': stripe_amount,
        'updated_amount_display': price_display(stripe_amount, rental_order.currency),
    }

    return payment_info


def sale_payment_info(sale_offer, user):
    payment_info = {}

    if sale_offer.price_usd < user.coastalbucket.balance:
        payment_info['payment_list'] = ['coastal', 'stripe']
        payment_info['coastal'] = {
            'coastal_dollar': '$%s' % format(int(user.coastalbucket.balance), ','),
            'amount': '$%s' % format(int(sale_offer.price_usd), ','),
        }
    else:
        payment_info['payment_list'] = ['stripe']

    stripe_amount = get_stripe_amount(sale_offer.price)  # add the stripe process fee
    payment_info['stripe'] = {
        'total_price': sale_offer.price,
        'total_price_display': sale_offer.get_price_display(),
        'updated_amount': stripe_amount,
        'updated_amount_display': price_display(stripe_amount, sale_offer.currency),
    }

    return payment_info
