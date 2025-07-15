import collections
from collections import abc

import fakeredis
import pytest

import sitecustomize  # noqa: F401
from unittest.mock import MagicMock
from django.conf import settings
from channels.layers import get_channel_layer

for name in ("MutableSet", "MutableMapping", "MutableSequence", "Mapping", "Iterable"):
    if not hasattr(collections, name):
        setattr(collections, name, getattr(abc, name))

def get_consumers_module():
    from ChatApp import consumers
    return consumers


class DummyRedis(fakeredis.FakeStrictRedis):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    redis_instance = DummyRedis()
    consumers = get_consumers_module()
    monkeypatch.setattr(consumers, "redis_client", redis_instance)
    monkeypatch.setattr(consumers.redis, "StrictRedis", lambda *a, **kw: redis_instance)
    return redis_instance


@pytest.fixture(autouse=True)
def disable_side_effects(monkeypatch):
    monkeypatch.setattr("ChatApp.audit.record_audit_event", lambda *a, **k: None)
    monkeypatch.setattr("ChatApp.tasks.send_push", lambda *a, **k: None)

    async def noop(*args, **kwargs):
        return None

    async def empty_list(*args, **kwargs):
        return []

    consumers = get_consumers_module()
    monkeypatch.setattr(consumers, "update_last_seen", noop)
    monkeypatch.setattr(consumers, "get_device_tokens", empty_list)


@pytest.fixture
def channel_layer_fixture():
    return get_channel_layer()


@pytest.fixture
def application():
    from WebSocketChatApp.routing import application
    return application


@pytest.fixture
def kms_client(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("boto3.client", lambda *a, **k: mock)
    monkeypatch.setattr("ChatApp.kms._kms_client", None, raising=False)
    return mock


@pytest.fixture(autouse=True)
def nightfall_mock(monkeypatch):
    mock = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {"findings": []}))
    monkeypatch.setattr("requests.post", mock)
    return mock


@pytest.fixture(autouse=True)
def settings_override(settings):
    settings.DEBUG = True
    settings.KMS_KEY_ID = "dummy"
    return settings
