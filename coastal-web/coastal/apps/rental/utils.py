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


def rental_out_date(product, start_datetime, end_datetime, rental_unit):
    start_out_date = RentalOutDate.objects.filter(end_date=start_datetime)
    end_out_date = RentalOutDate.objects.filter(start_date=end_datetime)
    if start_datetime < start_datetime.replace(hour=12):
        start_datetime = start_datetime.replace(hour=0)
    elif start_datetime > start_datetime.replace(hour=12):
        start_datetime = start_datetime.replace(hour=12)
    if end_datetime < end_datetime.replace(hour=12):
        end_datetime = end_datetime.replace(hour=12)
    elif end_datetime > end_datetime.replace(hour=12):
        end_datetime = end_datetime.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
    if start_out_date and end_out_date:
        start_out_date.update(end_date=end_out_date[0].end_date)
        end_out_date.delete()
    elif start_out_date:
        start_out_date.update(end_date=end_datetime)
    elif end_out_date:
        end_out_date.update(start_date=start_datetime)
    else:
        RentalOutDate.objects.create(product=product, start_date=start_datetime, end_date=end_datetime)

