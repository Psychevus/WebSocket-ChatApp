from datetime import timedelta
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch, MagicMock

from ChatApp.models import CustomUser, Conversation, Message


class ExpungeMessagesTestCase(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(email="e1@example.com", password="pass")
        self.user2 = CustomUser.objects.create_user(email="e2@example.com", password="pass")
        self.conversation = Conversation.objects.create(user1=self.user1, user2=self.user2, retention_days=1)

        old = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="old",
        )
        old.timestamp = timezone.now() - timedelta(days=2)
        old.save(update_fields=["timestamp"])
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="new",
        )

    @override_settings(EXPUNGE_S3_BUCKET=None)
    def test_expunge_old_messages(self):
        call_command('expunge_old_messages')
        msgs = list(self.conversation.messages.all())
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].content, 'new')

    @override_settings(EXPUNGE_S3_BUCKET='bucket')
    @patch('boto3.client')
    def test_export_to_s3(self, mock_client):
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        call_command('expunge_old_messages')
        mock_s3.put_object.assert_called()
