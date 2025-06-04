from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import boto3

from ChatApp.models import Conversation
from ChatApp.retention import cutoff_datetime


class Command(BaseCommand):
    help = "Delete messages older than the retention period and optionally export to S3"

    def handle(self, *args, **options):
        bucket = getattr(settings, 'EXPUNGE_S3_BUCKET', None)
        region = getattr(settings, 'AWS_REGION', 'us-east-1')
        s3_client = boto3.client('s3', region_name=region) if bucket else None

        for conversation in Conversation.objects.all():
            if conversation.legal_hold:
                continue
            cutoff = cutoff_datetime(conversation)
            old_messages = conversation.messages.filter(timestamp__lt=cutoff)
            if not old_messages.exists():
                continue
            if s3_client:
                lines = [
                    f"{m.timestamp.isoformat()} {m.sender.email}: {m.content}"
                    for m in old_messages.order_by('timestamp')
                ]
                key = f"chat_exports/{conversation.id}/{timezone.now().isoformat()}.txt"
                s3_client.put_object(Bucket=bucket, Key=key, Body="\n".join(lines).encode("utf-8"))
            old_messages.delete()
        self.stdout.write(self.style.SUCCESS("Expunge complete"))
