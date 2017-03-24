from django.contrib import admin
from coastal.apps.rental.models import *


class RentalOutDateAdmin(admin.ModelAdmin):

    list_display = ['product', 'start_date', 'end_date']


admin.site.register(BlackOutDate)
admin.site.register(RentalOrder)
admin.site.register(RentalOrderDiscount)
admin.site.register(ApproveEvent)
admin.site.register(PaymentEvent)
admin.site.register(RentalOutDate, RentalOutDateAdmin)
