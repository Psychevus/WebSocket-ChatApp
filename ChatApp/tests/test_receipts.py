from django.test import TestCase
from rest_framework.test import APIClient

from ChatApp.models import CustomUser, Conversation, Message, MessageReceipt


class ReceiptsAPITestCase(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(email='u1@example.com', password='pass')
        self.user2 = CustomUser.objects.create_user(email='u2@example.com', password='pass')
        self.conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        m1 = Message.objects.create(conversation=self.conv, sender=self.user2, content='hi')
        Message.objects.create(conversation=self.conv, sender=self.user2, content='again')
        MessageReceipt.objects.create(user=self.user1, conversation=self.conv, last_seen_id=m1.id)
        self.client = APIClient()
        self.client.login(email='u1@example.com', password='pass')

    def test_unread_count(self):
        resp = self.client.get('/api/receipts/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data[0]['conversation_id'], self.conv.id)
        self.assertEqual(data[0]['unread'], 1)
