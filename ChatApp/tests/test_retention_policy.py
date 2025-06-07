from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient

from ChatApp.models import CustomUser, Conversation, Message, RetentionPolicy


class RetentionPolicyCommandTestCase(TestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(email="a@example.com", password="pass")
        self.u2 = CustomUser.objects.create_user(email="b@example.com", password="pass")
        self.conversation = Conversation.objects.create(user1=self.u1, user2=self.u2)
        old = Message.objects.create(conversation=self.conversation, sender=self.u1, content="old")
        old.timestamp = timezone.now() - timedelta(hours=2)
        old.save(update_fields=["timestamp"])
        Message.objects.create(conversation=self.conversation, sender=self.u1, content="new")
        RetentionPolicy.objects.create(scope=str(self.conversation.id), ttl_seconds=3600)

    def test_apply_retention(self):
        call_command('apply_retention')
        msgs = list(Message.objects.filter(conversation=self.conversation))
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].content, 'new')


class RetentionPolicyAPITestCase(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email='admin@example.com', password='pass', is_staff=True)
        self.client = APIClient()
        self.client.login(email='admin@example.com', password='pass')

    def test_create_and_list_policy(self):
        resp = self.client.post('/api/retention/', {'scope': 'global', 'ttl_seconds': 60}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(RetentionPolicy.objects.count(), 1)
        resp = self.client.get('/api/retention/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

