import json
import logging

import boto3
from boto3.session import Session
from botocore.client import ClientError

from django.conf import settings
from coastal.apps.payment.utils import get_payment_info, sale_payment_info
from coastal.apps.sns.models import Token
from coastal.apps.sns.exceptions import NoEndpoint

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
            Token.objects.filter(user=receiver, endpoint=endpoint).delete()

        logger.debug('message: %s' % result_message)
        try:
            res = aws.publish(
                Message=json.dumps(result_message),
                TargetArn=endpoint,
                MessageStructure='json'
            )
            logger.debug('The response of publish message: \n%s' % res)
        except ClientError as e:
            logger.error(e)


def publish_message(content, dialogue_id, receiver_obj, sender_name):
    message = '%s: %s' % (sender_name, content[0:20])  # TODO: why 21?
    extra_attr = {
        'dialogue_id': dialogue_id,
        'type': 'message',
    }
    push_notification(receiver_obj, message, extra_attr)


# place an order
def publish_get_order(rental_order):
    owner = rental_order.owner
    message = 'You have a new rental request. You must confirm in 24 hours, or it will be cancelled automatically.'
    extra_attr = {
        'type': 'get_order',
        'rental_order_id': rental_order.id,
        'product_id': rental_order.product.id,
        'for_rental': rental_order.product.for_rental,
        'for_sale': rental_order.product.for_sale,
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image(),
    }
    push_notification(owner, message, extra_attr)


# after 24 hours order is invalid
def publish_unconfirmed_order(rental_order):
    owner = rental_order.owner
    guest = rental_order.guest
    message = 'The request has been cancelled, for the host didn\'t confirm in 24 hours.'
    extra_attr = {
        'type': 'unconfirmed_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image(),
    }
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# owner confirmed order
def publish_confirmed_order(rental_order):
    guest = rental_order.guest
    guest_message = 'Your request has been confirmed, please pay for it in 24 hours,' \
                    ' or it will be cancelled automatically.'
    product = rental_order.product
    extra_attr = {
        'type': 'confirmed_order',
        'is_rental': True,
        'rental_order_id': rental_order.id,
        'product_id': product.id,
        'product_name': product.name,
        'product_image': product.get_main_image(),
        'rental_order_status': rental_order.get_status_display(),
        'total_price_display': rental_order.get_total_price_display(),

    }
    extra_attr.update(get_payment_info(rental_order, rental_order.guest))
    push_notification(guest, guest_message, extra_attr)


# after 24 hours paid order is invalid
def publish_unpay_order(rental_order):
    owner = rental_order.owner
    guest = rental_order.guest
    message = 'Coastal has cancelled the request for you, for the guest hasn\'t finished ' \
              'the payment in 24 hours.'
    extra_attr = {
        'type': 'unpay_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image()
    }
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# guest successfully pay
def publish_paid_order(rental_order):
    owner = rental_order.owner
    host_message = 'The request becomes in transaction. We hope you enjoy using Coastal!'
    extra_attr = {
        'type': 'paid_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image(),
    }
    push_notification(owner, host_message, extra_attr)


# guest check in more than 24 hours
def publish_paid_owner_order(rental_order):
    owner = rental_order.owner
    message = 'Congratulations! You have earned $%s ' % rental_order.coastal_dollar
    extra_attr = {
        'type': 'check_in_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image()
    }
    push_notification(owner, message, extra_attr)


# guest check out
def publish_check_out_order(rental_order):
    guest = rental_order.guest
    message = 'Please check-out your rental.'
    extra_attr = {
        'type': 'check_out_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image(),
        'product_id': rental_order.product.id,
        'rental_order_id': rental_order.id,
    }
    push_notification(guest, message, extra_attr)


# owner refuse order
def publish_refuse_order(rental_order):
    guest = rental_order.guest
    message = 'Pity! Your request has been declined.'
    extra_attr = {
        'type': 'refuse_order',
        'product_name': rental_order.product.name,
        'product_image': rental_order.product.get_main_image(),
    }
    push_notification(guest, message, extra_attr)


# make an offer
def publish_new_offer(sale_offer):
    owner = sale_offer.owner
    message = 'You have received an offer on your listing! You must confirm in 24 hours, or it will be cancelled automatically.'
    product = sale_offer.product
    extra_attr = {
        'type': 'get_offer',
        'sale_offer_id': sale_offer.id,
        'product_id': product.id,
        'product_name': product.name,
        'product_image': product.get_main_image(),
        'for_rental': product.for_rental,
        'for_sale': product.for_sale,
    }
    push_notification(owner, message, extra_attr)


# owner confirmed order
def publish_confirmed_offer(sale_offer):
    guest = sale_offer.guest
    guest_message = 'Your offer has been confirmed, please pay for it in 24 hours,' \
                    ' or it will be cancelled automatically.'
    product = sale_offer.product
    extra_attr = {
        'type': 'confirmed_offer',
        'is_rental': False,
        'sale_offer_id': sale_offer.id,
        'product_id': product.id,
        'product_name': product.name,
        'product_image': product.get_main_image(),
        'sale_offer_status': sale_offer.get_status_display(),
        'total_price_display': sale_offer.get_price_display(),

    }
    extra_attr.update(sale_payment_info(sale_offer, guest))
    push_notification(guest, guest_message, extra_attr)


# owner refuse order
def publish_refuse_offer(sale_offer):
    guest = sale_offer.guest
    message = 'Pity! Your request has been declined.'
    extra_attr = {
        'type': 'refuse_order',
        'product_name': sale_offer.product.name,
        'product_image': sale_offer.product.get_main_image(),
    }
    push_notification(guest, message, extra_attr)


# after 24 hours offer is invalid
def publish_unconfirmed_offer(sale_offer):
    owner = sale_offer.owner
    guest = sale_offer.guest
    message = 'The offer has been cancelled, for the host didn\'t confirm in 24 hours.'
    extra_attr = {
        'type': 'unconfirmed_offer',
        'product_name': sale_offer.product.name,
        'product_image': sale_offer.product.get_main_image(),
    }
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# after 24 hours paid order is invalid
def publish_unpay_offer(sale_offer):
    owner = sale_offer.owner
    guest = sale_offer.guest
    message = 'Coastal has cancelled the offer for you, for the guest hasn\'t finished ' \
              'the payment in 24 hours.'
    extra_attr = {
        'type': 'unpay_offer',
        'product_name': sale_offer.product.name,
        'product_image': sale_offer.product.get_main_image()
    }
    push_notification(owner, message, extra_attr)
    push_notification(guest, message, extra_attr)


# guest check in more than 24 hours
def publish_paid_owner_offer(sale_offer):
    owner = sale_offer.owner
    message = 'Congratulations! You sold your listing %s, and you have earned $%s ' % (
        sale_offer.product.name, sale_offer.coastal_dollar)
    extra_attr = {
        'type': 'check_in_offer',
        'sale_offer_id': sale_offer.id,
        'product_name': sale_offer.product.name,
        'coastal_dollar': '$%s' % format(int(sale_offer.coastal_dollar), ','),
        'product': {
            'id': sale_offer.product.id,
            'name': sale_offer.product.name,
            'for_rental': sale_offer.product.for_rental,
            'for_sale': sale_offer.product.for_sale,
        },
        'guest': sale_offer.guest.basic_info(),
    }
    push_notification(owner, message, extra_attr)


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
    Token.objects.filter(token=token, user=user).delete()


# guest login success
def publish_log_in(user):
    message = 'Congratulations! You are logging in successfully'
    extra_attr = {}
    push_notification(user, message, extra_attr)
