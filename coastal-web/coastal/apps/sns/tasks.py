from celery import shared_task
from coastal.apps.sns.utils import re_push
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint
from coastal.apps.sns.models import Notification


@shared_task
def push_user_notifications(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return
    try:
        re_push(notification)
    except (NoEndpoint, DisabledEndpoint):
        pass
