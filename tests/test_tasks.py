from ChatApp import tasks
from importlib import reload
from ChatApp.models import Message, CustomUser, Conversation, MessageReceipt
from django.utils import timezone
import pytest


@pytest.mark.django_db
def test_purge_expired_messages():
    user = CustomUser.objects.create_user(email="u@x.com", password="p")
    convo = Conversation.objects.create(user1=user, user2=user)
    Message.objects.create(conversation=convo, sender=user, content="hi", expires_at=timezone.now()-timezone.timedelta(seconds=1))
    tasks.purge_expired_messages.run()
    assert Message.objects.count() == 0


@pytest.mark.django_db
def test_send_push(monkeypatch, settings):
    calls = {}
    reload(tasks)
    class DummyFCM:
        def __init__(self, api_key=None):
            pass
        def notify_multiple_devices(self, registration_ids, message_title, message_body):
            calls.setdefault('fcm', []).append(registration_ids)
    monkeypatch.setattr(tasks, 'FCMNotification', DummyFCM)
    class DummyClient:
        def send_notification(self, token, payload, topic):
            calls.setdefault('apns',[]).append(token)
    monkeypatch.setattr(tasks, 'APNsClient', lambda *a, **k: DummyClient())
    settings.FCM_SERVER_KEY = 'k'
    settings.APNS_CERT_FILE = 'c'
    settings.APNS_TOPIC = 't'
    tasks.send_push.run('t','b',[{'token':'a','platform':'android'},{'token':'b','platform':'ios'}])
    assert calls.get('fcm') == [['a']] and calls.get('apns') == ['b']


@pytest.mark.django_db
def test_erase_user_data():
    user = CustomUser.objects.create_user(email="u@x.com", password="p")
    convo = Conversation.objects.create(user1=user, user2=user)
    msg = Message.objects.create(conversation=convo, sender=user, content="hi")
    MessageReceipt.objects.create(user=user, conversation=convo, last_seen_id=msg.id)
    tasks.erase_user_data.run(user.id)
    assert not CustomUser.objects.filter(pk=user.id).exists()
    assert Conversation.objects.count() == 0
