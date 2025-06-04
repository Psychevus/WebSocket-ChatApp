from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from ChatApp.models import CustomUser, Conversation, Message, AuditLog

class AuditLogTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_superuser(email="admin@example.com", password="pass")
        self.user = CustomUser.objects.create_user(email="u@example.com", password="pass")
        self.conv = Conversation.objects.create(user1=self.admin, user2=self.user)

    @patch('ChatApp.audit._get_producer', return_value=None)
    def test_audit_log_created_on_message(self, mock_prod):
        Message.objects.create(conversation=self.conv, sender=self.admin, content="hi")
        entry = AuditLog.objects.get()
        self.assertEqual(entry.action, "message_sent")
        self.assertEqual(entry.user, self.admin)
        self.assertTrue(entry.hash)
        self.assertEqual(entry.previous_hash, "")

        Message.objects.create(conversation=self.conv, sender=self.admin, content="hi again")
        logs = AuditLog.objects.order_by("timestamp")
        self.assertEqual(logs.count(), 2)
        first, second = logs
        self.assertEqual(second.previous_hash, first.hash)

    @patch('ChatApp.audit._get_producer', return_value=None)
    def test_audit_logs_view(self, mock_prod):
        Message.objects.create(conversation=self.conv, sender=self.admin, content="hi")
        self.client.login(username="admin@example.com", password="pass")
        response = self.client.get(reverse('audit_logs'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["action"], "message_sent")
