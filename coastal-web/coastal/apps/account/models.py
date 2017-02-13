import datetime
import hashlib
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from coastal.apps.product.models import Product


def basic_info(self, prefix=''):
    from coastal.apps.account.utils import secure_email

    info = cache.get('user_basic_info|%s' % self.id)
    if info is None:
        info = {
            'id': self.id,
            'name': self.first_name or secure_email(self.email),
            'photo': self.userprofile.photo and self.userprofile.photo.url or '',
        }

        cache.set('user_basic_info|%s' % self.id, info, 5 * 60)

    if prefix:
        return {'%s%s' % (prefix, k): v for k, v in info.items()}
    return info
User.basic_info = basic_info


@receiver(post_save, sender=User)
def clear_user_cache(sender, **kwargs):
    cache.delete('user_basic_info|%s' % kwargs['instance'].id)


class UserProfile(models.Model):
    state = (
        ('unconfirmed', 'unconfirmed'),
        ('sending', 'sending'),
        ('confirmed', 'confirmed'),
    )
    CLIENT_CHOICES = (
        ('', '-------'),
        ('facebook', 'Facebook'),
    )

    user = models.OneToOneField(User)
    is_agent = models.NullBooleanField()
    agency_email = models.EmailField(max_length=128, null=True, blank=True)
    agency_name = models.CharField(max_length=128, null=True, blank=True)
    agency_address = models.CharField(max_length=256, null=True, blank=True)
    photo = models.ImageField(upload_to='user/%Y/%m', null=True, blank=True)
    email_confirmed = models.CharField(max_length=32, choices=state, blank=True, default='unconfirmed')
    stripe_customer_id = models.CharField(max_length=255, blank=True, default='')
    client = models.CharField(max_length=20, default='', blank=True, choices=CLIENT_CHOICES)
    invite_code = models.CharField(max_length=32, blank=True)

    @property
    def has_agency_info(self):
        return self.is_agent is not None


@receiver(post_save, sender=UserProfile)
def clear_user_profile_cache(sender, **kwargs):
    cache.delete('user_basic_info|%s' % kwargs['instance'].user.id)


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
    created_date = models.DateTimeField(auto_now_add=True)

    def create_token(self, user):
        token = user.email + str(timezone.now())
        md5token = hashlib.md5()
        md5token.update(token.encode('utf-8'))
        token = md5token.hexdigest()
        return token

    def create_date(self):
        now = timezone.now()
        tomorrow = now + datetime.timedelta(days=1)
        return tomorrow

    def save(self, user, *args, **kwargs):
        self.user = user
        self.token = self.create_token(user)
        self.expiration_date = self.create_date()
        super(ValidateEmail, self).save(*args, **kwargs)


class CoastalBucket(models.Model):
    user = models.OneToOneField(User)
    balance = models.FloatField(default=0)
    date_updated = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('in', 'in'),
        ('out', 'out'),
    )
    bucket = models.ForeignKey(CoastalBucket)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    order_number = models.CharField(max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)


class InviteCode(models.Model):
    user = models.ForeignKey(User, related_name='user_invite_code')
    referrer = models.ForeignKey(User, related_name='referrer_invite_code')
    invite_code = models.CharField(max_length=32)
    date_create = models.DateTimeField(auto_now_add=True)
