from celery import shared_task
from django.utils import timezone

import logging
from django.conf import settings
from ChatApp.models import Message
from pyfcm import FCMNotification
from apns2.client import APNsClient
from apns2.payload import Payload

@shared_task
def purge_expired_messages():
    Message.objects.filter(
        expires_at__isnull=False,
        expires_at__lte=timezone.now()
    ).delete()


@shared_task
def send_push(title: str, body: str, tokens: list):
    logger = logging.getLogger(__name__)

    android = [t["token"] for t in tokens if t.get("platform") == "android"]
    ios = [t["token"] for t in tokens if t.get("platform") == "ios"]

    if android and getattr(settings, "FCM_SERVER_KEY", None):
        try:
            fcm = FCMNotification(api_key=settings.FCM_SERVER_KEY)
            fcm.notify_multiple_devices(
                registration_ids=android, message_title=title, message_body=body
            )
        except Exception as e:
            logger.error(f"FCM error: {e}")

    if ios and getattr(settings, "APNS_CERT_FILE", None):
        try:
            client = APNsClient(
                settings.APNS_CERT_FILE,
                use_sandbox=getattr(settings, "APNS_USE_SANDBOX", True),
            )
            payload = Payload(alert={"title": title, "body": body})
            for token in ios:
                client.send_notification(token, payload, settings.APNS_TOPIC)
        except Exception as e:
            logger.error(f"APNS error: {e}")
