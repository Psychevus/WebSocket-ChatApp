from datetime import timedelta
from django.utils import timezone
from django.test import TestCase

from ChatApp.models import CustomUser, Conversation, Message
from ChatApp.tasks import purge_expired_messages

class EphemeralMessageTestCase(TestCase):
    def test_purge_expired_messages(self):
        user1 = CustomUser.objects.create_user(email="eph1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="eph2@example.com", password="pass")
        convo = Conversation.objects.create(user1=user1, user2=user2)
        expired = Message.objects.create(
            conversation=convo,
            sender=user1,
            content="gone",
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        purge_expired_messages()
        self.assertFalse(Message.objects.filter(id=expired.id).exists())
