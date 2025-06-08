import json
import os
import zipfile
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

from ChatApp.models import CustomUser, Conversation, Message, MessageReceipt


class ExportUserDataCommandTest(TestCase):
    def test_export_user_data(self):
        user = CustomUser.objects.create_user(email="exp@example.com", password="pass")
        other = CustomUser.objects.create_user(email="o@example.com", password="pass")
        conv = Conversation.objects.create(user1=user, user2=other)
        msg = Message.objects.create(conversation=conv, sender=user, content="hi")
        MessageReceipt.objects.create(user=user, conversation=conv, last_seen_id=msg.id)

        call_command("export_user_data", "exp@example.com")
        fname = f"user_{user.id}_data.zip"
        self.assertTrue(os.path.exists(fname))
        with zipfile.ZipFile(fname) as zf:
            data = json.loads(zf.read("data.json").decode())
        self.assertEqual(data["profile"]["fields"]["email"], "exp@example.com")
        self.assertEqual(len(data["messages"]), 1)
        os.remove(fname)


class GdprEraseAPITest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="gdpr@example.com", password="pass")
        self.client = APIClient()
        self.client.login(email="gdpr@example.com", password="pass")

    @patch("ChatApp.tasks.erase_user_data.apply_async")
    def test_schedule_erase(self, mock_apply):
        resp = self.client.post("/api/gdpr/erase/", {"confirm": "wrong"}, format="json")
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post("/api/gdpr/erase/", {"confirm": "gdpr@example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        mock_apply.assert_called_once()
        args, kwargs = mock_apply.call_args
        self.assertEqual(args[0][0], self.user.id)
        self.assertEqual(kwargs.get("countdown"), 30 * 24 * 60 * 60)
        self.user.refresh_from_db()
        self.assertTrue(self.user.pending_erasure)
