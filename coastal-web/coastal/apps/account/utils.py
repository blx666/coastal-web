from django.contrib.auth.models import User
from coastal.apps.account.models import UserProfile, CoastalBucket


def create_user(email, password=None):
    user = User.objects.create_user(username=email, email=email, password=password)
    UserProfile.objects.create(user=user)
    CoastalBucket.objects.create(user=user)
    return user


def is_confirmed_user(user):
    return user.get_full_name() and user.userprofile.email_confirmed and user.userprofile.photo
