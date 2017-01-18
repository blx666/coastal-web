from coastal.apps.rental.models import BlackOutDate,RentalOrder
from coastal.apps.rental.models import RentalOutDate
from coastal.apps.product import defines as defs
import datetime


def validate_rental_date(product, start_date, end_date):
    """The function will update the RentalDateRange values according to Black-Out Dates and Rental Orders.
       So when user update Black-Out Dates or Rental Order is created, please call the function.
    """
    black_out_dates = BlackOutDate.objects.filter(product=product, start_date__gte=start_date).filter(end_date__lte=end_date)
    rental_dates = RentalOrder.objects.filter(product=product, start_datetime__gte=start_date).filter(end_datetime__lte=end_date)
    return black_out_dates or rental_dates


def rental_out_date(product, start_datetime, end_datetime):
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
