from celery import shared_task
from coastal.apps.sns.utils import re_push
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint
from coastal.apps.sns.models import Notification
from django.contrib.auth.models import User


@shared_task
def push_user_notifications(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    notifications = Notification.objects.filter(user=user, pushed=False)
    if notifications:
        for notification in notifications:
            try:
                re_push(notification)
            except (NoEndpoint, DisabledEndpoint):
                pass
