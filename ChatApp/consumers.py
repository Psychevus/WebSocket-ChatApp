import asyncio
import json
import logging
from datetime import datetime
from django.core.cache import cache
import redis
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


def check_rate_limit(rate, method='RATELIMIT_KEY'):
    def decorator(func):
        async def wrapper(self, text_data):
            data = json.loads(text_data)
            message_content = data['message']

            sender = self.scope.get('user')

            if await self.is_ratelimited(sender, int(rate)):
                await asyncio.sleep(5)
                await self.send(text_data=json.dumps({
                    "message": "Rate limit exceeded. Please wait before sending another message."
                }))
                return

            await func(self, text_data)

        return wrapper

    return decorator


class ChatConsumer(AsyncWebsocketConsumer):
    async def is_ratelimited(self, user, rate):
        user_id = int(user.id) if user.id else None

        cache_key = f'rate_limit_{user_id}'

        if cache_key not in cache:
            cache.set(cache_key, 0, rate)

        if cache.get(cache_key) >= rate:
            return True

        cache.incr(cache_key)
        return False

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.conversation_group_name = f"chat_{self.conversation_id}"

        logger.info("ChatConsumer connect called")

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
        message_content = data['message']

        sender = self.scope.get('user')

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        logger.info(f"Received message: '{message_content}' from User {sender}")

        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat.message',
                'message': message_content,
                'sender_id': sender.id if sender else None,
                'sender_email': sender.email if sender else None,
                'timestamp': timestamp,
            }
        )

        try:
            conversation_key = f"conversation_{self.conversation_id}"
            message_data = {
                'message': message_content,
                'sender_id': sender.id if sender else None,
                'sender_email': sender.email if sender else None,
                'timestamp': timestamp,
            }

            message_json = json.dumps(message_data)
            redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)
            redis_client.lpush(conversation_key, message_json)

        except (redis.ConnectionError, Exception) as e:
            logger.error(f"An error occurred while storing the message in Redis: {str(e)}")
        finally:
            redis_client.close()

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({
            "message": message,
            "sender_id": event.get("sender_id"),
            "sender_email": event.get("sender_email"),
            "timestamp": event["timestamp"],
        }))
