import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from ChatApp.middleware import DLPWebSocketMiddleware
from django.core.asgi import get_asgi_application
from django.urls import re_path

from ChatApp import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebSocketChatApp.settings')

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/huddle/$', consumers.HuddleConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        DLPWebSocketMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
