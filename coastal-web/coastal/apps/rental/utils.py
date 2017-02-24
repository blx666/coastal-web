from coastal.apps.rental.models import BlackOutDate,RentalOrder
from coastal.apps.rental.models import RentalOutDate
from coastal.apps.product import defines as defs
import datetime
from django.utils import timezone


def validate_rental_date(product, start_date, end_date):
    """The function will update the RentalDateRange values according to Black-Out Dates and Rental Orders.
       So when user update Black-Out Dates or Rental Order is created, please call the function.
    """
    black_out_dates = BlackOutDate.objects.filter(product=product, start_date__gte=start_date).filter(end_date__lte=end_date)
    rental_dates = RentalOrder.objects.filter(product=product, start_datetime__gte=start_date).filter(end_datetime__lte=end_date)
    return black_out_dates or rental_dates


def insert_rental_out_date(product, start, end, start_extend=None, end_extend=None):
    if not start_extend:
        start_extend = start
    if not end_extend:
        end_extend = end

    start_out_date = RentalOutDate.objects.filter(start_date__lte=start_extend, end_date__gte=start_extend,
                                                  product=product)
    end_out_date = RentalOutDate.objects.filter(
        start_date__lte=end_extend, end_date__gte=end_extend, product=product).order_by('-end_date')
    if start_out_date and end_out_date:
        new_end_date = end_out_date[0].end_date
        end_out_date.delete()
        start_out_date.update(end_date=new_end_date)
        return start_out_date.first()
    elif start_out_date:
        start_out_date.update(end_date=end)
        return start_out_date.first()
    elif end_out_date:
        end_out_date.update(start_date=start)
        return end_out_date.first()
    else:
        return RentalOutDate.objects.create(product=product, start_date=start, end_date=end)


def update_rental_out_date(out_date, start, end, start_extend=None, end_extend=None):
    if not start_extend:
        start_extend = start
    if not end_extend:
        end_extend = end

    start_out_date = RentalOutDate.objects.filter(start_date__lte=start_extend, end_date__gte=start_extend,
                                                  product=out_date.product)
    end_out_date = RentalOutDate.objects.filter(
        start_date__lte=end_extend, end_date__gte=end_extend, product=out_date.product).order_by('-end_date')
    if start_out_date and end_out_date:
        start_out_date.update(end_date=end_out_date[0].end_date)
        end_out_date.delete()
        out_date.delete()
    elif start_out_date:
        start_out_date.update(end_date=end)
        out_date.delete()
    elif end_out_date:
        end_out_date.update(start_date=start)
        out_date.delete()
    else:
        out_date.start_date = start
        out_date.end_date = end
        out_date.save()


def rental_out_date(product, start_datetime, end_datetime):
    start_datetime = timezone.localtime(start_datetime)
    end_datetime = timezone.localtime(end_datetime)
    if product.category_id == defs.CATEGORY_ADVENTURE:
        if product.exp_time_unit == 'hour':
            if start_datetime.hour - product.exp_time_length < product.exp_start_time.hour:
                start_datetime = start_datetime.replace(hour=0)
                start_extend = start_datetime
            else:
                start_extend = start_datetime - datetime.timedelta(hours=product.exp_time_length) + datetime.timedelta(seconds=1)

            if end_datetime.hour + product.exp_time_length > product.exp_end_time.hour:
                end_datetime = end_datetime.replace(hour=0) + datetime.timedelta(days=1)
                end_extend = end_datetime
            else:
                end_extend = end_datetime + datetime.timedelta(hours=product.exp_time_length) - datetime.timedelta(seconds=1)
        else:
            extend_mapping = {
                'day': {
                    'days': product.exp_time_length,
                },
                'week': {
                    'days': product.exp_time_length * 7,
                }
            }
            extend_time = datetime.timedelta(**extend_mapping[product.exp_time_unit])
            start_extend = start_datetime - extend_time
            end_extend = end_datetime + extend_time
        insert_rental_out_date(product, start_datetime, end_datetime, start_extend, end_extend)

    else:
        if start_datetime.hour < 12:
            start_datetime = start_datetime.replace(hour=0)
        elif start_datetime.hour > 12:
            start_datetime = start_datetime.replace(hour=12)
        if end_datetime.hour < 12:
            end_datetime = end_datetime.replace(hour=12)
        elif end_datetime.hour > 12:
            end_datetime = end_datetime.replace(hour=0) + datetime.timedelta(days=1)

        start_out_date = RentalOutDate.objects.filter(end_date=start_datetime, product=product)
        end_out_date = RentalOutDate.objects.filter(start_date=end_datetime, product=product)

        if start_out_date and end_out_date:
            start_out_date.update(end_date=end_out_date[0].end_date)
            end_out_date.delete()
        elif start_out_date:
            start_out_date.update(end_date=end_datetime)
        elif end_out_date:
            end_out_date.update(start_date=start_datetime)
        else:
            RentalOutDate.objects.create(product=product, start_date=start_datetime, end_date=end_datetime)


def clean_rental_out_date(product, start_datetime, end_datetime):
    if product.category_id == defs.CATEGORY_ADVENTURE:
        today_begin = start_datetime.replace(hour=0, minute=0, second=0)
        today_end = today_begin + datetime.timedelta(days=1)
        rental_date = RentalOutDate.objects.filter(start_date=today_begin, end_date=today_end, product=product)
        if rental_date:
            rental_date.delete()
            rental_order = RentalOrder.objects.filter(product=product).exclude(status='declined')
            for order in rental_order:
                if order.end_datetime > datetime.datetime.now().replace(hour=0, minute=0, second=0):
                    rental_out_date(product, order.start_datetime, order.end_datetime)
        else:
            rental_date = RentalOutDate.objects.filter(start_date=start_datetime, end_date=end_datetime, product=product)
            if rental_date:
                rental_date.delete()
            rental_date = RentalOutDate.objects.filter(start_date__lt=start_datetime, end_date__gt=end_datetime, product=product)
            if rental_date:
                end_date = rental_date[0].end_date
                RentalOutDate.objects.create(product=product, start_date=end_datetime,end_date=end_date)
                rental_date.update(end_date=start_datetime)
            rental_date = RentalOutDate.objects.filter(start_date=start_datetime,end_date__gt=end_datetime, product=product)
            if rental_date:
                rental_date.update(start_date=end_datetime)
            rental_date = RentalOutDate.objects.filter(start_date__lt=start_datetime, end_date=end_datetime, product=product)
            if rental_date:
                rental_date.update(end_date=start_datetime)
    else:
        if start_datetime.hour < 12:
            start_datetime = start_datetime.replace(hour=0)
        elif start_datetime.hour > 12:
            start_datetime = start_datetime.replace(hour=12)
        if end_datetime.hour < 12:
            end_datetime = end_datetime.replace(hour=12)
        elif end_datetime.hour > 12:
            end_datetime = end_datetime.replace(hour=0) + datetime.timedelta(days=1)
        rental_date = RentalOutDate.objects.filter(start_date=start_datetime,end_date=end_datetime, product=product)
        if rental_date:
            rental_date.delete()
        rental_date = RentalOutDate.objects.filter(start_date__lt=start_datetime,end_date__gt=end_datetime, product=product)
        if rental_date:
            end_date = rental_date[0].end_date
            RentalOutDate.objects.create(product=product, start_date=end_datetime,end_date=end_date)
            rental_date.update(end_date=start_datetime)
        rental_date = RentalOutDate.objects.filter(start_date=start_datetime,end_date__gt=end_datetime, product=product)
        if rental_date:
            rental_date.update(start_date=end_datetime)
        rental_date = RentalOutDate.objects.filter(start_date__lt=start_datetime, end_date=end_datetime, product=product)
        if rental_date:
            rental_date.update(end_date=start_datetime)


def recreate_rental_out_date(product):
    rental_date = RentalOutDate.objects.filter(product=product)
    if rental_date:
        rental_date.delete()
        rental_order = RentalOrder.objects.filter(product=product).exclude(status__in=RentalOrder.INVALID_STATUS_LIST)
        for order in rental_order:
            if order.end_datetime.replace(tzinfo=None) > datetime.datetime.now().replace(hour=0, minute=0, second=0):
                rental_out_date(product, order.start_datetime, order.end_datetime)
