from coastal.apps.rental.models import BlackOutDate, RentalOrder


def update_rental_available_dates(product, start_datetime, end_datetime):
    """The function will update the RentalDateRange values according to Black-Out Dates and Rental Orders.
       So when user update Black-Out Dates or Rental Order is created, please call the function.
    """
    RentalOrder.objects.filter(product=product, start_datetime__lte=start_datetime,end_datetime__gte=start_datetime)
    RentalOrder.objects.filter(product=product, start_datetime__lte=end_datetime,end_datetime__gte=end_datetime)
    BlackOutDate.objects.filter(product=product, start_date__lte=start_datetime.date(),
                                      end_dat__gte=start_datetime.date())
    BlackOutDate.objects.filter(product=product, start_date__lte=start_datetime.date(),
                                      end_dat__gte=start_datetime.date())
    pass
