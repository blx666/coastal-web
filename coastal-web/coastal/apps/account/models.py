from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product
import hashlib
from datetime import datetime, timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    is_agent = models.NullBooleanField()
    agency_email = models.EmailField(max_length=128, null=True, blank=True)
    agency_name = models.CharField(max_length=128, null=True, blank=True)
    agency_address = models.CharField(max_length=256, null=True, blank=True)
    photo = models.ImageField(upload_to='user/%Y/%m', null=True, blank=True)
    email_confirmed = models.BooleanField(default=False)

    @property
    def has_agency_info(self):
        return self.is_agent is not None


class Favorites(models.Model):
    user = models.ForeignKey(User, related_name='favorites')

    class Meta:
        verbose_name_plural = 'Favorites'


class FavoriteItem(models.Model):
    favorite = models.ForeignKey(Favorites, related_name='items')
    product = models.ForeignKey(Product)


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, related_name='recently_viewed')
    product = models.ForeignKey(Product)
    date_created = models.DateTimeField(auto_now_add=True)


class ValidateEmail(models.Model):
    user = models.ForeignKey(User)
    token = models.CharField(null=True, unique=True, max_length=256)
    expiration_date = models.DateTimeField()

    def create_token(self, user):
        token = user.email + str(datetime.now())
        md5token = hashlib.md5()
        md5token.update(token.encode('utf-8'))
        token = md5token.hexdigest()
        return token

    def create_date(self):
        now = datetime.now().replace(tzinfo=None)
        tomorrow = now + timedelta(days=1)
        return tomorrow

    def save(self, user, *args, **kwargs):
        self.user = user
        self.token = self.create_token(user)
        self.expiration_date = self.create_date()
        super(ValidateEmail, self).save(*args, **kwargs)







