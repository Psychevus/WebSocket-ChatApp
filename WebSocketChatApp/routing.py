import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from ChatApp.middleware import (
    DLPWebSocketMiddleware,
    JWTAuthMiddleware,
    WebSocketRateLimitMiddleware,
)
from django.core.asgi import get_asgi_application
from django.urls import re_path
from django.conf import settings

from ChatApp import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebSocketChatApp.settings')

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/rooms/(?P<room_id>\w+)/$', consumers.ChatRoomConsumer.as_asgi()),
    re_path(r'ws/huddle/$', consumers.HuddleConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": OriginValidator(
            JWTAuthMiddleware(
                WebSocketRateLimitMiddleware(
                    DLPWebSocketMiddleware(
                        URLRouter(websocket_urlpatterns)
                    )
                )
            ),
            getattr(settings, "WEBSOCKET_ALLOWED_ORIGINS", []),
        ),
    }
)
