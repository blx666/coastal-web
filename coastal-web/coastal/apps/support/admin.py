from django.contrib import admin
from coastal.apps.support.models import Report


class ReportAdmin(admin.ModelAdmin):
    list_display = ['product', 'status', 'user']

admin.site.register(Report, ReportAdmin)

