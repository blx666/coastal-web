from coastal.apps.sale.models import SaleOffer
from coastal.apps.rental.models import RentalOrder
from coastal.apps.product.models import Product
from django.template import loader
from django.core.mail import EmailMessage
from django.conf import settings
from celery import shared_task


@shared_task
def send_transaction_email(product_id, order_id, flag):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return
    if flag == 'rental':
        try:
            order = RentalOrder.objects.get(id=order_id)
        except RentalOrder.DoesNotExist:
            return
    else:
        try:
            order = SaleOffer.objects.get(id=order_id)
        except SaleOffer.DoesNotExist:
            return

    subject = '[ItsCoastal]Transaction Reminder'
    if settings.DEBUG:
        mail_list = settings.TEST_TO_EMAIL
    else:
        mail_list = settings.LIVE_TO_EMAIL
    host_account = order.owner.email
    guest_account = order.guest.email
    date = order.date_updated.strftime('%m/%d/%Y')
    html_content = loader.render_to_string('send-trade-email.html', {
        'name': product.name,
        'type': product.category.name,
        'host_account': host_account,
        'guest_account': guest_account,
        'date': date,
    })
    msg = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, mail_list)
    msg.content_subtype = "html"
    msg.send()
