from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from unittest.mock import patch, MagicMock

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation, Message

class MessageSanitizationTestCase(TransactionTestCase):
    def test_html_stripped(self):
        user1 = CustomUser.objects.create_user(email="san1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="san2@example.com", password="pass")
        convo = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            with patch('ChatApp.consumers.redis.StrictRedis') as mock_redis:
                mock_redis.return_value.__enter__.return_value = MagicMock()

                communicator = WebsocketCommunicator(application, f"ws/chat/{convo.id}/")
                communicator.scope['user'] = user1

                connected, _ = await communicator.connect()
                assert connected

                await communicator.send_json_to({'message': '<b>Hello</b>'})
                response = await communicator.receive_json_from()
                assert response['message'] == 'Hello'

                await communicator.disconnect()

        async_to_sync(inner)()

        self.assertEqual(Message.objects.first().content, 'Hello')

    @override_settings(MESSAGE_MAX_LENGTH=10)
    def test_length_limit(self):
        user1 = CustomUser.objects.create_user(email="long1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="long2@example.com", password="pass")
        convo = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            communicator = WebsocketCommunicator(application, f"ws/chat/{convo.id}/")
            communicator.scope['user'] = user1

            connected, _ = await communicator.connect()
            assert connected

            await communicator.send_json_to({'message': 'x' * 11})
            response = await communicator.receive_json_from()
            assert response['message'] == 'Message too long.'

            await communicator.disconnect()

        async_to_sync(inner)()
