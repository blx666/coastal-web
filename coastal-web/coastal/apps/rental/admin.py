from django.contrib import admin
from coastal.apps.rental.models import RentalDateRange, BlackOutDate

admin.site.register(RentalDateRange)
admin.site.register(BlackOutDate)
