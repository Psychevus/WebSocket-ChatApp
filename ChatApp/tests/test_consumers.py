from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from unittest.mock import patch, MagicMock

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation, Message


class ChatConsumerTestCase(TransactionTestCase):
    def test_message_persistence(self):
        user1 = CustomUser.objects.create_user(email="cuser1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="cuser2@example.com", password="pass")
        conversation = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            with patch('ChatApp.consumers.redis.StrictRedis') as mock_redis:
                mock_client = MagicMock()
                mock_redis.return_value.__enter__.return_value = mock_client

                communicator = WebsocketCommunicator(application, f"ws/chat/{conversation.id}/")
                communicator.scope['user'] = user1

                connected, _ = await communicator.connect()
                assert connected

                await communicator.send_json_to({'message': 'hello'})
                response = await communicator.receive_json_from()
                assert response['message'] == 'hello'

                await communicator.disconnect()

        async_to_sync(inner)()

        self.assertTrue(
            Message.objects.filter(
                conversation=conversation,
                sender=user1,
                content='hello'
            ).exists()
        )

    def test_typing_indicator_broadcast(self):
        user1 = CustomUser.objects.create_user(email="tuser1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="tuser2@example.com", password="pass")
        conversation = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            communicator1 = WebsocketCommunicator(application, f"ws/chat/{conversation.id}/")
            communicator1.scope['user'] = user1
            communicator2 = WebsocketCommunicator(application, f"ws/chat/{conversation.id}/")
            communicator2.scope['user'] = user2

            connected, _ = await communicator1.connect()
            assert connected
            connected, _ = await communicator2.connect()
            assert connected

            await communicator1.send_json_to({'type': 'typing'})
            response = await communicator2.receive_json_from()
            assert response['type'] == 'typing'
            assert response['sender_email'] == user1.email

            await communicator1.disconnect()
            await communicator2.disconnect()

        async_to_sync(inner)()
