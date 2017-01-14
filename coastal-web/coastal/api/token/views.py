from boto3.session import Session
import boto3
from coastal.api.core import response
from coastal.api.core.response import CoastalJsonResponse
from django.conf import settings
from coastal.apps.sns.models import Token


def bind_token(request):
    token = request.GET.get('token')
    uuid = request.GET.get('uuid')
    if not (token and uuid):
        return CoastalJsonResponse(status=response.STATUS_400)

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
    Token.objects.update_or_create(uuid=uuid, defaults={'user': request.user, 'token': token,
                                                        'endpoint': endpoint_arn, 'uuid': uuid})

    result = {
        'endpoint_arn': endpoint_arn,
    }

    return CoastalJsonResponse(result)