import os
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from unittest.mock import patch

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation
from ChatApp.dlp import run_dlp_hook


def block_if_contains_forbidden(message, sender=None):
    return False if "FORBIDDEN" in message else True


class DLPHookTestCase(TransactionTestCase):
    @override_settings(DLP_BEFORE_SEND_HOOK='ChatApp.tests.test_dlp.block_if_contains_forbidden')
    def test_dlp_blocks_message(self):
        user1 = CustomUser.objects.create_user(email="dlp1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="dlp2@example.com", password="pass")
        conversation = Conversation.objects.create(user1=user1, user2=user2)

        async def inner():
            communicator = WebsocketCommunicator(application, f"ws/chat/{conversation.id}/")
            communicator.scope['user'] = user1

            connected, _ = await communicator.connect()
            assert connected

            await communicator.send_json_to({'message': 'FORBIDDEN text'})
            response = await communicator.receive_json_from()
            assert response['message'] == 'Message blocked by DLP policy.'

            await communicator.disconnect()

        async_to_sync(inner)()


class NightfallDLPHookTestCase(TransactionTestCase):
    @patch('ChatApp.dlp_plugins.requests.post')
    def test_nightfall_scan_plugin(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'findings': ['ssn']}

        with patch.dict(os.environ, {'NIGHTFALL_API_KEY': 'dummy'}):
            result = async_to_sync(run_dlp_hook)(
                'SSN 123-45-6789',
                None,
                'ChatApp.dlp_plugins.nightfall_scan'
            )
            self.assertFalse(result)

