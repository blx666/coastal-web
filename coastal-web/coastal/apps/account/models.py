from django.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    is_agent = models.NullBooleanField()
    agency_email = models.EmailField(max_length=128, null=True, blank=True)
    agency_name = models.CharField(max_length=128, null=True, blank=True)
    agency_address = models.CharField(max_length=256, null=True, blank=True)
    photo = models.ImageField(upload_to='user/%Y/%m', null=True, blank=True)

    @property
    def has_agency_info(self):
        return self.is_agent is not None


class Favorites(models.Model):
    user = models.ForeignKey(User, related_name='favorites')

    class Meta:
        verbose_name_plural = 'Favorites'


class FavoriteItem(models.Model):
    favorite = models.ForeignKey(Favorites, related_name='items')
    product = models.OneToOneField(Product)
