from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from unittest.mock import patch, MagicMock

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation


class WebSocketIntegrationTests(TransactionTestCase):
    def test_websocket_message_exchange(self):
        user1 = CustomUser.objects.create_user(email="u1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="u2@example.com", password="pass")
        convo = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            with patch("ChatApp.consumers.redis.StrictRedis") as mock_redis:
                mock_client = MagicMock()
                mock_redis.return_value.__enter__.return_value = mock_client

                comm1 = WebsocketCommunicator(application, f"ws/chat/{convo.id}/")
                comm1.scope["user"] = user1
                comm2 = WebsocketCommunicator(application, f"ws/chat/{convo.id}/")
                comm2.scope["user"] = user2

                connected, _ = await comm1.connect()
                assert connected
                connected, _ = await comm2.connect()
                assert connected

                await comm1.send_json_to({"message": "hello"})
                response = await comm2.receive_json_from()
                assert response["message"] == "hello"

                await comm1.disconnect()
                await comm2.disconnect()

        async_to_sync(inner)()

    def test_message_delivery_ordering(self):
        from django.utils import timezone
        from ChatApp.models import Message

        user1 = CustomUser.objects.create_user(email="o1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="o2@example.com", password="pass")
        convo = Conversation.objects.create(user1=user1, user2=user2)

        times = [timezone.now(), timezone.now() + timezone.timedelta(seconds=1), timezone.now() + timezone.timedelta(seconds=2)]
        contents = ["first", "second", "third"]
        for t, c in zip(times, contents):
            Message.objects.create(conversation=convo, sender=user1, content=c, timestamp=t)

        messages = list(convo.messages.values_list("content", flat=True))
        assert messages == contents
