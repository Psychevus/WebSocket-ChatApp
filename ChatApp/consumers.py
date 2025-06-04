import asyncio
import json
import logging
import redis
import bleach

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone

from django.conf import settings
from .models import Conversation, Message
from .dlp import run_dlp_hook

logger = logging.getLogger(__name__)


def check_rate_limit(rate, method='RATELIMIT_KEY'):
    def decorator(func):
        async def wrapper(self, text_data):
            sender = self.scope.get('user')

            if await self.is_ratelimited(sender, int(rate)):
                await asyncio.sleep(5)
                await self.send_json({
                    "message": "Rate limit exceeded. Please wait before sending another message."
                })
                return

            await func(self, text_data)

        return wrapper

    return decorator


class ChatConsumer(AsyncWebsocketConsumer):
    async def before_send(self, message: str, sender):
        hook = getattr(settings, 'DLP_BEFORE_SEND_HOOK', 'ChatApp.dlp.default_dlp_callback')
        return await run_dlp_hook(message, sender, hook)

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))
    async def is_ratelimited(self, user, rate):
        user_id = int(user.id) if user.id else None
        cache_key = f'rate_limit_{user_id}'

        remaining_requests = cache.get_or_set(cache_key, rate, rate)

        if remaining_requests <= 0:
            return True

        cache.decr(cache_key)

        return False

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.conversation_group_name = f"chat_{self.conversation_id}"

        logger.info("ChatConsumer connect called")

        if not self.scope.get('user') or not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.scope['user']} connected to conversation {self.conversation_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )
        logger.info(f"User {self.scope['user']} disconnected from conversation {self.conversation_id}")

    @check_rate_limit(rate=1)
    async def receive(self, text_data: str):
        data = json.loads(text_data)

        if data.get('type') == 'typing':
            sender = self.scope.get('user')
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat.typing',
                    'sender_id': sender.id if sender else None,
                    'sender_email': sender.email if sender else None,
                }
            )
            return

        if data.get('type') == 'public_key':
            sender = self.scope.get('user')
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat.public_key',
                    'sender_id': sender.id if sender else None,
                    'sender_email': sender.email if sender else None,
                    'key': data.get('key'),
                }
            )
            return

        ciphertext = data.get('ciphertext')
        nonce = data.get('nonce')
        ephemeral = data.get('ephemeral')
        message_content = data.get('message', '')

        if not ciphertext:
            # Clean message content to avoid XSS when not encrypted
            message_content = bleach.clean(
                message_content, tags=[], attributes={}, strip=True
            )

            if len(message_content) > getattr(settings, 'MESSAGE_MAX_LENGTH', 500):
                await self.send_json({
                    "message": "Message too long."
                })
                return
        sender = self.scope.get('user')
        timestamp = timezone.now()
        expires_at = None
        if ephemeral:
            ttl = int(getattr(settings, 'EPHEMERAL_MESSAGE_TTL', '30'))
            expires_at = timestamp + timezone.timedelta(seconds=ttl)

        logger.info(f"Received message: '{message_content}' from User {sender}")

        if not await self.before_send(message_content, sender):
            await self.send_json({"message": "Message blocked by DLP policy."})
            return

        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat.message',
                'message': message_content,
                'nonce': nonce,
                'sender_id': sender.id if sender else None,
                'sender_email': sender.email if sender else None,
                'timestamp': timestamp.isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
            }
        )

        try:
            conversation_key = f"conversation_{self.conversation_id}"
            message_data = {
                'message': message_content,
                'nonce': nonce,
                'sender_id': sender.id if sender else None,
                'sender_email': sender.email if sender else None,
                'timestamp': timestamp.isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
            }

            message_json = json.dumps(message_data)

            with redis.StrictRedis(host="localhost", port=6379, db=0) as redis_client:
                redis_client.lpush(conversation_key, message_json)

            conversation = await database_sync_to_async(Conversation.objects.get)(pk=self.conversation_id)
            await database_sync_to_async(Message.objects.create)(
                conversation=conversation,
                sender=sender,
                content=message_content,
                timestamp=timestamp,
                expires_at=expires_at,
            )

        except (redis.ConnectionError, Exception) as e:
            logger.error(f"An error occurred while storing the message in Redis or DB: {str(e)}")

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({
            "message": message,
            "nonce": event.get("nonce"),
            "sender_id": event.get("sender_id"),
            "sender_email": event.get("sender_email"),
            "timestamp": event["timestamp"],
            "expires_at": event.get("expires_at"),
        }))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "sender_id": event.get("sender_id"),
            "sender_email": event.get("sender_email"),
        }))

    async def chat_public_key(self, event):
        await self.send(text_data=json.dumps({
            "type": "public_key",
            "sender_id": event.get("sender_id"),
            "sender_email": event.get("sender_email"),
            "key": event.get("key"),
        }))

