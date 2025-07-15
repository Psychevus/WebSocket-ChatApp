import json
from unittest.mock import MagicMock

import pytest

from ChatApp.models import CustomUser, Conversation
from ChatApp.views import fetch_messages_from_redis


@pytest.mark.django_db
def test_fetch_messages_from_redis(monkeypatch):
    user1 = CustomUser.objects.create_user(email="a@example.com", password="pass")
    user2 = CustomUser.objects.create_user(email="b@example.com", password="pass")
    convo = Conversation.objects.create(user1=user1, user2=user2)

    data = [
        json.dumps({"message": "hi", "timestamp": "2023-01-01 00:00:00.000000"}),
        json.dumps({"message": "bye", "timestamp": "2023-01-01 00:01:00.000000"}),
    ]

    class DummyRedis:
        def __init__(self, *args, **kwargs):
            pass
        def lrange(self, *args, **kwargs):
            return [d.encode("utf-8") for d in data]
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("ChatApp.views.redis.StrictRedis", lambda *a, **kw: DummyRedis())

    messages = fetch_messages_from_redis(convo)
    assert len(messages) == 2
    assert messages[0]["message"] == "hi"
    assert messages[1]["message"] == "bye"
