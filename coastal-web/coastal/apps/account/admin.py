from django.contrib import admin
from coastal.apps.account.models import UserProfile, Favorites, FavoriteItem, RecentlyViewed, ValidateEmail, \
    CoastalBucket, Transaction, InviteRecord, InviteCode


class InviteRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'referrer', 'invite_code', 'date_create']


class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ['invite_code', 'used']

admin.site.register(UserProfile)
admin.site.register(Favorites)
admin.site.register(FavoriteItem)
admin.site.register(RecentlyViewed)
admin.site.register(ValidateEmail)
admin.site.register(CoastalBucket)
admin.site.register(Transaction)
admin.site.register(InviteRecord, InviteRecordAdmin)
admin.site.register(InviteCode, InviteCodeAdmin)
