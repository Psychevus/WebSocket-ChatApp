import asyncio
import json
import logging
import redis
import bleach

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from opentelemetry import trace

from django.conf import settings
from .models import (
    Conversation,
    Message,
    DeviceToken,
    ChatRoom,
    RoomMessage,
)
from .models import MessageReceipt
from .tasks import send_push
from .dlp import run_dlp_hook
from WebSocketChatApp.telemetry import record_websocket_latency

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

redis_client = redis.Redis(
    host=getattr(settings, "REDIS_HOST", "localhost"),
    port=int(getattr(settings, "REDIS_PORT", 6379)),
    decode_responses=True,
)


@database_sync_to_async
def register_conversation(cid: str, user_id: int):
    try:
        backend = settings.CHANNEL_LAYERS["default"].get("BACKEND", "")
        if backend.endswith("InMemoryChannelLayer"):
            return
        redis_client.sadd("active_conversations", cid)
        redis_client.sadd(f"active_conversation_users:{cid}", user_id)
    except Exception:
        pass


@database_sync_to_async
def unregister_conversation(cid: str, user_id: int):
    try:
        backend = settings.CHANNEL_LAYERS["default"].get("BACKEND", "")
        if backend.endswith("InMemoryChannelLayer"):
            return
        redis_client.srem(f"active_conversation_users:{cid}", user_id)
        if redis_client.scard(f"active_conversation_users:{cid}") == 0:
            redis_client.srem("active_conversations", cid)
    except Exception:
        pass


@database_sync_to_async
def update_last_seen(user_id: int, conversation_id: int, message_id: int):
    receipt, _ = MessageReceipt.objects.get_or_create(
        user_id=user_id, conversation_id=conversation_id
    )
    if message_id > receipt.last_seen_id:
        receipt.last_seen_id = message_id
        receipt.save(update_fields=["last_seen_id", "updated_at"])


@database_sync_to_async
def get_device_tokens(user_id: int):
    return list(DeviceToken.objects.filter(user_id=user_id).values("token", "platform"))


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
        with tracer.start_as_current_span("connect"):
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

        await register_conversation(str(self.conversation_id), self.scope['user'].id)

        await self.accept()
        self.last_activity = timezone.now()
        self.presence_task = asyncio.create_task(self.presence_loop())
        logger.info(
            f"User {self.scope['user']} connected to conversation {self.conversation_id}"
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )
        await unregister_conversation(str(self.conversation_id), self.scope['user'].id)
        if hasattr(self, "presence_task"):
            self.presence_task.cancel()
        logger.info(f"User {self.scope['user']} disconnected from conversation {self.conversation_id}")

    @check_rate_limit(rate=1)
    async def receive(self, text_data: str):
        with tracer.start_as_current_span("receive"):
            self.last_activity = timezone.now()
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

            try:
                with tracer.start_as_current_span("db_write"):
                    conversation_key = f"conversation_{self.conversation_id}"
                    conversation = await database_sync_to_async(Conversation.objects.get)(pk=self.conversation_id)
                    msg = await database_sync_to_async(Message.objects.create)(
                        conversation=conversation,
                        sender=sender,
                        content=message_content,
                        timestamp=timestamp,
                        expires_at=expires_at,
                    )

                    message_data = {
                        'id': msg.id,
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

                await update_last_seen(sender.id, self.conversation_id, msg.id)

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
                        'message_id': msg.id,
                    }
                )

                recipient = conversation.user2 if conversation.user1_id == sender.id else conversation.user1
                offline = not redis_client.sismember(
                    f"active_conversation_users:{self.conversation_id}", recipient.id
                )
                if offline:
                    tokens = await get_device_tokens(recipient.id)
                    if tokens:
                        send_push.delay(
                            f"New message from {sender.email}", message_content, tokens
                        )

            except (redis.ConnectionError, Exception) as e:
                logger.error(f"An error occurred while storing the message in Redis or DB: {str(e)}")

    async def chat_message(self, event):
        message = event["message"]

        start_time = timezone.datetime.fromisoformat(event["timestamp"])
        latency_ms = (timezone.now() - start_time).total_seconds() * 1000
        record_websocket_latency(latency_ms)

        if event.get("message_id"):
            await update_last_seen(self.scope["user"].id, self.conversation_id, event["message_id"])

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

    async def chat_pre_stop(self, event):
        await self.close(code=1001)

    async def chat_presence_update(self, event):
        await self.send_json({"type": "presence_update", "user_id": event.get("user_id")})

    async def presence_loop(self):
        try:
            while True:
                await asyncio.sleep(15)
                if (timezone.now() - self.last_activity).total_seconds() > 45:
                    await self.close()
                    break
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {"type": "chat.presence_update", "user_id": self.scope["user"].id},
                )
        except asyncio.CancelledError:
            pass


from .huddle.rooms import create_room


class HuddleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope.get("user") or not self.scope["user"].is_authenticated:
            await self.close()
            return
        await self.accept()

    async def receive(self, text_data: str):
        data = json.loads(text_data)
        if data.get("action") == "start_huddle":
            room = create_room()
            await self.send(text_data=json.dumps({
                "type": "huddle_started",
                "roomId": room.id,
                "routerRtpCapabilities": room.router_rtp_capabilities,
            }))


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat.room.{self.room_id}"

        if not self.scope.get("user") or not self.scope["user"].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data: str):
        data = json.loads(text_data)
        message = bleach.clean(data.get("message", ""))
        sender = self.scope.get("user")
        timestamp = timezone.now()

        room = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_id)
        await database_sync_to_async(RoomMessage.objects.create)(
            room=room, sender=sender, content=message, timestamp=timestamp
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room.message",
                "message": message,
                "sender_id": sender.id if sender else None,
                "sender_email": sender.email if sender else None,
                "timestamp": timestamp.isoformat(),
            },
        )

    async def room_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender_id": event.get("sender_id"),
            "sender_email": event.get("sender_email"),
            "timestamp": event.get("timestamp"),
        }))
