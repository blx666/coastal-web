import json
import logging

import boto3
from boto3.session import Session
from botocore.client import ClientError

from django.conf import settings
from coastal.apps.sns.models import Token
from coastal.apps.sns.exceptions import NoEndpoint, DisabledEndpoint

logger = logging.getLogger(__name__)


def push_notification(receiver, content, extra_attr=None):
    aws_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    region_name = settings.REGION
    Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    boto3.setup_default_session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    aws = boto3.client('sns')

    notification = {
        'aps': {
            'alert': content,
            'sound': 'default'
        },
    }

    if extra_attr:
        notification.update(extra_attr)

    if settings.DEBUG:
        result_message = {
            'APNS_SANDBOX': json.dumps(notification)
        }
    else:
        result_message = {
            'APNS': json.dumps(notification)
        }

    # TODO: can we set the endpoint to cache?
    endpoint_list = Token.objects.filter(user=receiver).values_list('endpoint', flat=True)
    if not endpoint_list:
        raise NoEndpoint

    for endpoint in endpoint_list:
        logger.debug('Endpoint: %s' % endpoint)
        endpoint_attributes = aws.get_endpoint_attributes(
            EndpointArn=endpoint,
        )

        enabled = endpoint_attributes['Attributes']['Enabled']
        if enabled == 'false':
            raise DisabledEndpoint

        res = aws.publish(
            Message=json.dumps(result_message),
            TargetArn=endpoint,
            MessageStructure='json'
        )
        logger.debug('The response of publish message: \n%s' % res)


def publish_message(content, dialogue_id, receiver_obj, sender_name):
    message = '%s: %s' % (sender_name, content[0:20])  # TODO: why 21?
    extra_attr = {
        'dialogue_id': dialogue_id,
        'type': 'message',
    }
    push_notification(receiver_obj, message, extra_attr)


# place an order
def publish_get_order(rental_order, message, extra_attr):
    owner = rental_order.owner
    push_notification(owner, message, extra_attr)


# after 24 hours order is invalid
def publish_unconfirmed_order(rental_order, message, extra_attr):
    owner = rental_order.owner
    guest = rental_order.guest
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# owner confirmed order
def publish_confirmed_order(rental_order, guest_message, extra_attr):
    guest = rental_order.guest
    push_notification(guest, guest_message, extra_attr)


# after 24 hours paid order is invalid
def publish_unpay_order(rental_order, message, extra_attr):
    owner = rental_order.owner
    guest = rental_order.guest
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# guest successfully pay
def publish_paid_order(rental_order, extra_attr):
    owner = rental_order.owner
    host_message = 'The request becomes in transaction. We hope you enjoy using Coastal!'
    push_notification(owner, host_message, extra_attr)


# guest check in more than 24 hours
def publish_check_in_order(rental_order, message, extra_attr):
    owner = rental_order.owner
    push_notification(owner, message, extra_attr)


# guest check out
def publish_check_out_order(rental_order, message, extra_attr):
    guest = rental_order.guest
    push_notification(guest, message, extra_attr)


# owner refuse order
def publish_refuse_order(rental_order, message, extra_attr):
    guest = rental_order.guest
    push_notification(guest, message, extra_attr)


def bind_token(uuid, token, user):
    aws_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    region_name = settings.REGION
    Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    boto3.setup_default_session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    aws = boto3.client('sns')

    token_obj = Token.objects.filter(token=token).first()
    if not token_obj:
        try:
            endpoint = aws.create_platform_endpoint(
                PlatformApplicationArn=settings.PLATFORM_APPLICATION_ARN,
                Token=token
            )
        except ClientError as e:
            logger.error('Create Platform Endpoint on AWS: %s \n %s' % (token, e))
            return

        endpoint_arn = endpoint['EndpointArn']
    else:
        endpoint_arn = token_obj.endpoint
    Token.objects.update_or_create(token=token, defaults={'user': user, 'token': token, 'endpoint': endpoint_arn,
                                                          'uuid': uuid})


# TODO
def unbind_token(token, user):
    pass
