from django.contrib import admin
from coastal.apps.rental.models import *

admin.site.register(BlackOutDate)
admin.site.register(RentalOrder)
admin.site.register(RentalOrderDiscount)
admin.site.register(ApproveEvent)
admin.site.register(PaymentEvent)
admin.site.register(RentalOutDate)
