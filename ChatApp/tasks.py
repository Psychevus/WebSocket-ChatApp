from celery import shared_task
from django.utils import timezone

from ChatApp.models import Message

@shared_task
def purge_expired_messages():
    Message.objects.filter(
        expires_at__isnull=False,
        expires_at__lte=timezone.now()
    ).delete()
