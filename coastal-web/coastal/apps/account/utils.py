import re
from django.contrib.auth.models import User
from coastal.apps.account.models import UserProfile, CoastalBucket


def create_user(email, password=None):
    user = User.objects.create_user(username=email.lower(), email=email, password=password)
    UserProfile.objects.create(user=user)
    CoastalBucket.objects.create(user=user)
    return user


def is_confirmed_user(user):
    if not user.get_full_name():
        return False
    if not user.userprofile.photo:
        return False
    if user.userprofile.email_confirmed != 'confirmed':
        return False
    return True


def secure_email(email):
    pattern = re.compile('^(.{1,3}).*@(.*)$')
    return '***@'.join(pattern.match(email).groups())
