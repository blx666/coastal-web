from django.contrib import admin
from coastal.apps.rental.models import RentalDateRange, BlackOutDate, RentalOrder

admin.site.register(RentalDateRange)
admin.site.register(BlackOutDate)
admin.site.register(RentalOrder)
