from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ChatApp.models import Message, RetentionPolicy


class Command(BaseCommand):
    help = "Purge messages based on RetentionPolicy settings"

    def handle(self, *args, **options):
        now = timezone.now()
        for policy in RetentionPolicy.objects.all():
            if policy.override_until and now < policy.override_until:
                continue
            cutoff = now - timedelta(seconds=policy.ttl_seconds)
            try:
                shard_id = int(policy.scope)
                qs = Message.objects.filter(conversation_id=shard_id, timestamp__lt=cutoff)
            except ValueError:
                qs = Message.objects.filter(timestamp__lt=cutoff)
            deleted, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(f"Purged {deleted} messages for scope {policy.scope}"))
