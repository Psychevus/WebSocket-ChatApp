import logging
import collections
from collections import abc as collections_abc

from apns2.client import APNsClient
from apns2.payload import Payload
from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from pyfcm import FCMNotification

from ChatApp.models import Message, CustomUser, MessageReceipt, Conversation

for name in (
    "MutableSet",
    "MutableMapping",
    "MutableSequence",
    "Mapping",
    "Iterable",
):
    if not hasattr(collections, name):
        setattr(collections, name, getattr(collections_abc, name))

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

@shared_task
def erase_user_data(user_id: int):
    """Delete a user's personal data."""
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return

    MessageReceipt.objects.filter(user=user).delete()
    Message.objects.filter(
        Q(sender=user) | Q(conversation__user1=user) | Q(conversation__user2=user)
    ).delete()
    Conversation.objects.filter(Q(user1=user) | Q(user2=user)).delete()
    user.first_name = ""
    user.last_name = ""
    user.email = f"deleted-{user.id}@example.com"
    user.is_active = False
    user.pending_erasure = False
    user.save(update_fields=["first_name", "last_name", "email", "is_active", "pending_erasure"])

