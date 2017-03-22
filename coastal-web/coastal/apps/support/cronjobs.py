import datetime
from django.utils import timezone
from django.template import loader
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from coastal.apps.product import defines as defs
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.sale.models import SaleOffer


def send_daily_report():
    subject = '[ItsCoastal]Daily Report'
    bbc = []
    if settings.DEBUG:
        send_email = settings.TEST_TO_EMAIL
    else:
        send_email = settings.LIVE_TO_EMAIL
        bbc = settings.BBC_LIVE_TO_EMAIL
    time = timezone.now()
    week_day = int(time.strftime('%w'))
    month_day = int(time.strftime('%d'))

    day_time = timezone.now().date() + timezone.timedelta(days=0)
    month_time = day_time - timezone.timedelta(days=month_day)
    week_time = day_time - timezone.timedelta(days=week_day)
    week_time_v2 = day_time - timezone.timedelta(days=week_day+1)
    last_day_time = day_time - timezone.timedelta(days=1)
    last_week_time = week_time - timezone.timedelta(days=7)
    last_month_time = (datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1)

    daily_growth = Product.objects.filter(active_product__gte=day_time)
    month_growth = Product.objects.filter(active_product__gte=month_time)
    week_growth = Product.objects.filter(active_product__gte=week_time)
    last_daily_growth = Product.objects.filter(Q(active_product__lte=day_time) & Q(active_product__gt=last_day_time))
    last_week_growth = Product.objects.filter(Q(active_product__lte=week_time) & Q(active_product__gt=last_week_time))
    last_month_growth = Product.objects.filter(Q(active_product__lte=month_time) & Q(active_product__gt=last_month_time))

    transaction_daily_growth = RentalOrder.objects.filter(date_succeed__gte=day_time).count() + SaleOffer.objects.filter(date_succeed__gte=day_time).count()
    transaction_week_growth = RentalOrder.objects.filter(date_succeed__gte=week_time).count() + SaleOffer.objects.filter(date_succeed__gte=week_time).count()
    transaction_month_growth = RentalOrder.objects.filter(date_succeed__gte=month_time).count() + SaleOffer.objects.filter(date_succeed__gte=month_time).count()
    transaction_last_daily_growth = RentalOrder.objects.filter(Q(date_succeed__lte=day_time) & Q(date_succeed__gt=last_day_time)).count() + SaleOffer.objects.filter(Q(date_succeed__lte=day_time) & Q(date_succeed__gt=last_day_time)).count()
    transaction_last_week_growth = RentalOrder.objects.filter(Q(date_succeed__lte=week_time) & Q(date_succeed__gt=last_week_time)).count() + SaleOffer.objects.filter(Q(date_succeed__lte=week_time) & Q(date_succeed__gt=last_week_time)).count()
    transaction_last_month_growth = RentalOrder.objects.filter(Q(date_succeed__lte=month_time) & Q(date_succeed__gt=last_month_time)).count() + SaleOffer.objects.filter(Q(date_succeed__lte=month_time) & Q(date_succeed__gt=last_month_time)).count()

    time_list = [daily_growth, last_daily_growth, week_growth, last_week_growth, month_growth, last_month_growth]
    day_time_display = day_time.strftime('%m/%d')
    last_day_time_display = last_day_time.strftime('%m/%d')
    week_time_display = '%s-%s' % (week_time.strftime('%m/%d'), day_time_display)
    last_week_time_display = '%s-%s' % (last_week_time.strftime('%m/%d'), week_time_v2.strftime('%m/%d'))
    month_time_display = '%s-%s' % (datetime.date.today().replace(day=1).strftime('%m/%d/%Y'), day_time.strftime('%m/%d/%Y'))
    last_month_time_display = '%s-%s' % (last_month_time.strftime('%m/%d/%Y'), month_time.strftime('%m/%d/%Y'))
    data = []

    category = [defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT, defs.CATEGORY_ROOM, defs.CATEGORY_YACHT,
                defs.CATEGORY_BOAT_SLIP, defs.CATEGORY_JET, defs.CATEGORY_ADVENTURE]
    for i in category:
        for y in time_list:
            data.append(y.filter(category_id=i).count())
        data.append(Product.objects.filter(category_id=i).count())
    data.append(transaction_daily_growth)
    data.append(transaction_last_daily_growth)
    data.append(transaction_week_growth)
    data.append(transaction_last_week_growth)
    data.append(transaction_month_growth)
    data.append(transaction_last_month_growth)
    data.append(RentalOrder.objects.all().count() + SaleOffer.objects.all().count())
    product = ['House', 'Apartment', 'Room', 'Yacht', 'Boat Slip', 'Aircraft', 'Adventure', 'Transaction']
    html_content = loader.render_to_string('send-daily-report.html', {
        'product': product,
        'house': data[0:7],
        'apartment': data[7:14],
        'room': data[14:21],
        'yacht': data[21:28],
        'boat_slip': data[28:35],
        'aircraft': data[35:42],
        'adventure': data[42:49],
        'transaction': data[49:56],
        'day_time_display': day_time_display,
        'last_day_time_display': last_day_time_display,
        'week_time_display': week_time_display,
        'last_week_time_display': last_week_time_display,
        'month_time_display': month_time_display,
        'last_month_time_display': last_month_time_display,
    })
    msg = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, send_email, bbc)
    msg.content_subtype = "html"
    msg.send()
