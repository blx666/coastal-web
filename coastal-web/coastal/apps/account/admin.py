from django.contrib import admin
from coastal.apps.account.models import UserProfile, Favorites, FavoriteItem, RecentlyViewed, ValidateEmail

admin.site.register(UserProfile)
admin.site.register(Favorites)
admin.site.register(FavoriteItem)
admin.site.register(RecentlyViewed)
admin.site.register(ValidateEmail)