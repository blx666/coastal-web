import django
import os
import sys

from coastal.apps.rental.models import RentalOutDate, RentalOrder
from coastal.apps.rental.utils import rental_out_date
from coastal.apps.product import defines as defs

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coastal.settings")
django.setup()


def rebuild_rental_out_data():
    RentalOutDate.objects.filter(product__category_id=defs.CATEGORY_ADVENTURE).delete()
    rental_order = RentalOrder.objects.filter(product__category_id=defs.CATEGORY_ADVENTURE).exclude(status__in=RentalOrder.INVALID_STATUS_LIST)
    for order in rental_order:
        rental_out_date(order.product, order.start_datetime, order.end_datetime)

if __name__ == '__main__':
    rebuild_rental_out_data()
