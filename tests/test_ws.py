import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from unittest.mock import patch, MagicMock

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation


@pytest.mark.django_db(transaction=True)
def test_basic_websocket_flow():
    user1 = CustomUser.objects.create_user(email="ws1@example.com", password="pass")
    user2 = CustomUser.objects.create_user(email="ws2@example.com", password="pass")
    convo = Conversation.objects.create(user1=user1, user2=user2)

    async def inner():
        with patch("ChatApp.consumers.redis.StrictRedis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value.__enter__.return_value = mock_client

            communicator = WebsocketCommunicator(application, f"ws/chat/{convo.id}/")
            communicator.scope["user"] = user1

            connected, _ = await communicator.connect()
            assert connected

            await communicator.send_json_to({"message": "hello"})
            response = await communicator.receive_json_from()
            assert response["message"] == "hello"

            await communicator.disconnect()

    async_to_sync(inner)()
