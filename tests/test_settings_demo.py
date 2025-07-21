import importlib
import sys
import types

import pytest


def test_settings_demo_import(monkeypatch):
    class DummyCelery:
        def __init__(self, *a, **k):
            pass

        def config_from_object(self, *a, **k):
            pass

        def autodiscover_tasks(self):
            pass

    monkeypatch.setitem(sys.modules, 'celery', types.SimpleNamespace(Celery=DummyCelery))
    module = importlib.import_module('WebSocketChatApp.settings_demo')

    assert module.DEBUG is True
    assert module.USE_DEV_AUTH is True
    assert module.CELERY_BROKER_URL is None
    assert module.ALLOWED_HOSTS == ['*']
    assert module.WEBSOCKET_ALLOWED_ORIGINS == ['*']
