import pytest
import fakeredis
from ChatApp import consumers

class DummyRedis(fakeredis.FakeStrictRedis):
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    redis_instance = DummyRedis()
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
    monkeypatch.setattr("ChatApp.consumers.update_last_seen", noop)
    monkeypatch.setattr("ChatApp.consumers.get_device_tokens", empty_list)
