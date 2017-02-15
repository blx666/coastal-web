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


def rental_out_date(product, start_datetime, end_datetime):
    if product.category_id == defs.CATEGORY_EXPERIENCE:
        start_out_date = RentalOutDate.objects.filter(end_date=start_datetime, product=product)
        end_out_date = RentalOutDate.objects.filter(start_date=end_datetime, product=product)
        if product.exp_time_unit != 'hour':
            if start_out_date and end_out_date:
                start_out_date.update(end_date=end_out_date[0].end_date)
                end_out_date.delete()
            elif start_out_date:
                start_out_date.update(end_date=end_datetime)
            elif end_out_date:
                end_out_date.update(start_date=start_datetime)
            else:
                RentalOutDate.objects.create(product=product, start_date=start_datetime, end_date=end_datetime)
        else:
            if start_out_date and end_out_date:
                start_out_date.update(end_date=end_out_date[0].end_date)
                end_out_date.delete()
            elif start_out_date:
                start_out_date.update(end_date=end_datetime)
            elif end_out_date:
                end_out_date.update(start_date=start_datetime)
            else:
                RentalOutDate.objects.create(product=product, start_date=start_datetime, end_date=end_datetime)
            today_begin = timezone.localtime(start_datetime, timezone.get_current_timezone()).replace(hour=0, minute=0, second=0)
            today_end = today_begin + datetime.timedelta(days=1)
            product_start = today_begin.replace(hour=product.exp_start_time.hour,minute=product.exp_start_time.minute)
            product_end = today_begin.replace(hour=product.exp_end_time.hour,minute=product.exp_end_time.minute)
            rental_date = RentalOutDate.objects.filter(product=product, start_date__gte=today_begin,
                                                       end_date__lte=today_end).order_by('start_date')
            product_seconds = product.exp_time_length * 60 * 60
            if rental_date.count() > 1:
                seconds = [(rental_date[0].start_date-product_start).seconds, (product_end - rental_date[rental_date.count()-1].end_date).seconds]
                for i in range(len(rental_date)-2):
                    seconds.append((rental_date[i+1].start_date - rental_date[i].end_date).seconds)
                if min(seconds) < product_seconds:
                    rental_date.delete()
                    RentalOutDate.objects.create(product=product, start_date=today_begin, end_date=today_end)
            else:
                if (rental_date[0].start_date-product_start).seconds < product_seconds and (product_end - rental_date[0].end_date).seconds < product_seconds:
                    rental_date.delete()
                    RentalOutDate.objects.create(product=product, start_date=today_begin,end_date=today_end)
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
    if product.category_id == defs.CATEGORY_EXPERIENCE:
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
        rental_order = RentalOrder.objects.filter(product=product).exclude(status='declined')
        for order in rental_order:
            if order.end_datetime.replace(tzinfo=None) > datetime.datetime.now().replace(hour=0, minute=0, second=0):
                rental_out_date(product, order.start_datetime, order.end_datetime)
