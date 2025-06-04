from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .models import Conversation


def get_retention_days(conversation: Conversation) -> int:
    if conversation.retention_days is not None:
        return conversation.retention_days
    return getattr(settings, 'WORKSPACE_RETENTION_DAYS', getattr(settings, 'ORG_RETENTION_DAYS', 30))


def cutoff_datetime(conversation: Conversation):
    return timezone.now() - timedelta(days=get_retention_days(conversation))
