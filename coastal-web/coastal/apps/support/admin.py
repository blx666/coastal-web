from django.contrib import admin
from coastal.apps.support.models import Report, Helpcenter


class ReportAdmin(admin.ModelAdmin):
    list_display = ['product', 'status', 'user']

admin.site.register(Report, ReportAdmin)


class HelpAdmin(admin.ModelAdmin):
    list_display = ['email', 'subject', 'content']
admin.site.register(Helpcenter, HelpAdmin)