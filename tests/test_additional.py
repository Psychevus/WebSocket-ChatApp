import json
from asgiref.sync import async_to_sync, sync_to_async
import pytest
import jwt
import redis
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from ChatApp import views, audit, tasks
from ChatApp.middleware import DLPWebSocketMiddleware, JWTAuthMiddleware
from ChatApp.huddle import rooms as huddle_rooms
from ChatApp.models import CustomUser, Conversation

@pytest.mark.django_db
def test_fetch_messages_from_redis_errors(monkeypatch):
    class DummyRedis:
        def __init__(self, fail=False, bad=False):
            self.fail = fail
            self.bad = bad
        def lrange(self, key, start, end):
            if self.fail:
                raise redis.ConnectionError("boom")
            if self.bad:
                return [b"not-json"]
            return [json.dumps({"message":"hi","timestamp":"2024-01-01 00:00:00.000000"}).encode()]
        def close(self):
            pass
    convo = Conversation.objects.create(user1=CustomUser.objects.create_user(email="a@b.com"), user2=CustomUser.objects.create_user(email="b@b.com"))
    monkeypatch.setattr(views.redis, "StrictRedis", lambda *a, **k: DummyRedis(fail=True))
    assert views.fetch_messages_from_redis(convo) == []
    monkeypatch.setattr(views.redis, "StrictRedis", lambda *a, **k: DummyRedis(bad=True))
    assert views.fetch_messages_from_redis(convo) == []
    monkeypatch.setattr(views.redis, "StrictRedis", lambda *a, **k: DummyRedis())
    msgs = views.fetch_messages_from_redis(convo)
    assert msgs and msgs[0]["message"] == "hi"

@pytest.mark.django_db
def test_audit_producer_errors(monkeypatch):
    monkeypatch.setattr(audit, "_producer", None)
    settings.KAFKA_BROKER_URL = "kafka:9092"
    class Boom(Exception):
        pass
    def bad_kafka(*a, **k):
        raise Boom()
    monkeypatch.setattr(audit, "KafkaProducer", bad_kafka)
    user = CustomUser.objects.create_user(email="u@x.com")
    audit.record_audit_event(user, "act", {"x":1})
    assert audit._producer is None
    class Dummy:
        def send(self, *a, **k):
            raise Boom()
    monkeypatch.setattr(audit, "_get_producer", lambda: Dummy())
    audit.record_audit_event(user, "act2", {"y":2})

@pytest.mark.django_db
def test_send_push_error_paths(monkeypatch, settings):
    settings.FCM_SERVER_KEY = "k"
    settings.APNS_CERT_FILE = "c"
    settings.APNS_TOPIC = "t"
    class BadFCM:
        def __init__(self, *a, **k):
            pass
        def notify_multiple_devices(self, *a, **k):
            raise RuntimeError("fail")
    class BadAPNS:
        def __init__(self, *a, **k):
            pass
        def send_notification(self, *a, **k):
            raise RuntimeError("fail")
    monkeypatch.setattr(tasks, "FCMNotification", lambda *a, **k: BadFCM())
    monkeypatch.setattr(tasks, "APNsClient", lambda *a, **k: BadAPNS())
    tasks.send_push("t", "b", [{"token":"a","platform":"android"},{"token":"b","platform":"ios"}])

@pytest.mark.django_db
def test_erase_user_data_missing(monkeypatch):
    tasks.erase_user_data.run(999)  # should not raise

@pytest.mark.asyncio
async def test_dlp_middleware_block(monkeypatch):
    sent = []
    async def app(scope, receive, send):
        await send({"type":"websocket.send","text":json.dumps({"message":"hi"})})
    middleware = DLPWebSocketMiddleware(app)
    async def fake_hook(*a, **k):
        return False
    monkeypatch.setattr('ChatApp.middleware.run_dlp_hook', fake_hook)
    async def capture(message):
        sent.append(message)
    await middleware({"user":object()}, lambda: None, capture)
    assert sent == []

@pytest.mark.asyncio
async def test_dlp_middleware_pass(monkeypatch):
    sent = []
    async def app(scope, receive, send):
        await send({"type":"websocket.send","text":"bad"})
    middleware = DLPWebSocketMiddleware(app)
    async def capture(message):
        sent.append(message)
    await middleware({"user":object()}, lambda: None, capture)
    assert sent

@pytest.mark.django_db
def test_jwt_middleware(monkeypatch):
    user = CustomUser.objects.create_user(email="tok@ex.com")
    token = jwt.encode({"user_id": user.id}, "secret", algorithm="HS256")
    scope = {"query_string": f"token={token}".encode()}
    async def inner(scope, receive, send):
        pass
    mw = JWTAuthMiddleware(inner)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "secret")
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256")
    async_to_sync(mw)(scope, lambda: None, lambda m: None)
    assert scope["user"].id == user.id
    def bad_decode(*a, **k):
        raise jwt.DecodeError("bad")
    monkeypatch.setattr(jwt, "decode", bad_decode)
    scope = {"headers": [(b"authorization", f"Bearer {token}".encode())]}
    async_to_sync(mw)(scope, lambda: None, lambda m: None)
    assert isinstance(scope["user"], AnonymousUser)


def test_create_room():
    room = huddle_rooms.create_room()
    assert room.id in huddle_rooms._rooms
    assert room.router_rtp_capabilities["codecs"]
