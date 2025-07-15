from django.core.handlers.asgi import ASGIHandler
from django.core.handlers.wsgi import WSGIHandler
from WebSocketChatApp import asgi, wsgi


def test_asgi_application_instance():
    assert isinstance(asgi.application, ASGIHandler)


def test_wsgi_application_instance():
    assert isinstance(wsgi.application, WSGIHandler)
