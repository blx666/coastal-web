import re
from django.contrib.auth.models import User
from django.utils import timezone
from coastal.apps.account.models import UserProfile, CoastalBucket, InviteRecord, Transaction
from coastal.apps.sns.utils import push_referrer_reward, push_user_reward
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint


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


def reward_invite_referrer(user):
    invite_record = InviteRecord.objects.filter(user=user).first()
    if invite_record and not invite_record.referrer_reward:
        referrer_bucket = invite_record.referrer.coastalbucket
        referrer_bucket.balance += 10
        referrer_bucket.save()

        Transaction.objects.create(bucket=referrer_bucket, type='in', note='invite_referrer', amount=10)

        invite_record.referrer_reward = timezone.now()
        invite_record.save()

        try:
            push_referrer_reward(invite_record.referrer)
        except (NoEndpoint, DisabledEndpoint):
            pass


def reward_invite_user(user):
    invite_record = InviteRecord.objects.filter(user=user).first()
    if invite_record and not invite_record.user_reward:
        user_bucket = invite_record.user.coastalbucket
        user_bucket.balance += 35
        user_bucket.save()

        Transaction.objects.create(bucket=user_bucket, type='in', note='invite_user', amount=35)

        invite_record.user_reward = timezone.now()
        invite_record.save()

        try:
            push_user_reward(user)
        except (NoEndpoint, DisabledEndpoint):
            pass
