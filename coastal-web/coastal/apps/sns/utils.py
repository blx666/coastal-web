from boto3.session import Session
import boto3,json
from django.conf import settings
from coastal.apps.sns.models import Token
from coastal.api.core.response import CoastalJsonResponse
from coastal.api.core import response


def publish_message(content, dialogue_id, receiver_obj, sender_name):
    aws_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    region_name = settings.REGION
    Session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    boto3.setup_default_session(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region_name)
    aws = boto3.client('sns')
    message = {
        'aps': {
            'alert': sender_name+':'+content[0:21],
            'sound': 'default'
        },
        'type': 'message',
        'dialogue_id': dialogue_id
    }
    result_message = {
        'APNS_SANDBOX': json.dumps(message),
        'APNS': json.dumps(message)
    }

    receiver_list = Token.objects.filter(user=receiver_obj)
    if not receiver_list:
        return CoastalJsonResponse(status=response.STATUS_404)
    for reciver in receiver_list:
        publish_message = aws.publish(
            Message=json.dumps(result_message),
            TargetArn=reciver.endpoint,
            MessageStructure='json'
        )


def to_bind_token(uuid, token, user):
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
