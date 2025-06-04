from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import redis

class Command(BaseCommand):
    help = "Notify all active WebSocket connections of shutdown"

    def handle(self, *args, **options):
        redis_host = getattr(settings, "REDIS_HOST", "localhost")
        redis_port = int(getattr(settings, "REDIS_PORT", 6379))
        client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        groups = client.smembers("active_conversations")
        channel_layer = get_channel_layer()
        for cid in groups:
            async_to_sync(channel_layer.group_send)(f"chat_{cid}", {"type": "chat.pre_stop"})
        self.stdout.write(self.style.SUCCESS("Sent shutdown to WebSocket groups"))

