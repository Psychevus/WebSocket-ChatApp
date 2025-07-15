import os
from django.core.management import call_command
from ChatApp.models import CustomUser, Conversation, Message, RetentionPolicy
from unittest.mock import MagicMock
from django.utils import timezone


import pytest


@pytest.mark.django_db
def test_create_dev_superuser(settings):
    os.environ['DEV_ADMIN_EMAIL'] = 'dev@example.com'
    os.environ['DEV_ADMIN_PASSWORD'] = 'pass'
    call_command('create_dev_superuser')
    assert CustomUser.objects.filter(email='dev@example.com').exists()


@pytest.mark.django_db
def test_apply_retention():
    user = CustomUser.objects.create_user(email='a@b.com', password='x')
    convo = Conversation.objects.create(user1=user, user2=user)
    msg = Message.objects.create(conversation=convo, sender=user, content='old', timestamp=timezone.now()-timezone.timedelta(days=10))
    RetentionPolicy.objects.create(scope=str(convo.id), ttl_seconds=0)
    call_command('apply_retention')
    assert Message.objects.count() == 0


@pytest.mark.django_db
def test_expunge_old_messages(monkeypatch):
    user = CustomUser.objects.create_user(email='a@b.com', password='x')
    convo = Conversation.objects.create(user1=user, user2=user, retention_days=1)
    msg = Message.objects.create(conversation=convo, sender=user, content='hi')
    msg.timestamp = timezone.now()-timezone.timedelta(days=2)
    msg.save(update_fields=['timestamp'])
    mock_s3 = MagicMock()
    monkeypatch.setattr('boto3.client', lambda *a, **k: mock_s3)
    call_command('expunge_old_messages')
    assert Message.objects.count() == 0


def test_pre_stop(monkeypatch):
    monkeypatch.setattr('redis.Redis.smembers', lambda *a, **k: {'1'})
    send_calls = []
    class DummyLayer:
        async def group_send(self, group, msg):
            send_calls.append((group, msg))
    monkeypatch.setattr('channels.layers.get_channel_layer', lambda: DummyLayer())
    call_command('pre_stop')
    assert send_calls
