import json
import logging

import boto3
from boto3.session import Session

from django.conf import settings
from coastal.apps.sns.models import Token
from coastal.apps.sns.expections import NoEndpoint, DisabledEndpoint

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
        'type': 'message',
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
    message = '%s: %s' % (sender_name, content[0:21])  # TODO: why 21?
    extra_attr = {
        'dialogue_id': dialogue_id
    }
    push_notification(receiver_obj, message, extra_attr)


def bind_token(uuid, token, user):
    aws_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    region_name = settings.REGION
    Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    boto3.setup_default_session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    aws = boto3.client('sns')

    token_obj = Token.objects.filter(uuid=uuid, token=token).first()
    if not token_obj:
        endpoint = aws.create_platform_endpoint(
            PlatformApplicationArn=settings.PLATFORM_APPLICATION_ARN,
            Token=token
        )
        endpoint_arn = endpoint['EndpointArn']
    else:
        endpoint_arn = token_obj.endpoint
    Token.objects.update_or_create(uuid=uuid, defaults={'user': user, 'token': token, 'endpoint': endpoint_arn,
                                                        'uuid': uuid})


# TODO
def unbind_token(token, user):
    pass
