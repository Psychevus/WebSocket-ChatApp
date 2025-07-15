import json
import logging
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.core.cache import cache
import jwt

from .dlp import run_dlp_hook

logger = logging.getLogger(__name__)


class DLPWebSocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message.get('type') == 'websocket.send' and 'text' in message:
                try:
                    payload = json.loads(message['text'])
                    msg_text = payload.get('message')
                except Exception:
                    msg_text = None
                if msg_text:
                    allow = await run_dlp_hook(
                        msg_text,
                        scope.get('user'),
                        getattr(settings, 'DLP_BEFORE_SEND_HOOK', 'ChatApp.dlp.default_dlp_callback'),
                    )
                    if not allow:
                        logger.info('Message blocked by DLP middleware')
                        return
            await send(message)

        return await super().__call__(scope, receive, send_wrapper)


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if not scope.get("user") or not getattr(scope.get("user"), "is_authenticated", False):
            token = None
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                from urllib.parse import parse_qs
                qs = parse_qs(query_string)
                token = qs.get("token", [None])[0]

            if not token:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization")
                if auth_header:
                    auth_value = auth_header.decode()
                    if auth_value.lower().startswith("bearer "):
                        token = auth_value.split(" ", 1)[1]

            if token:
                try:
                    payload = jwt.decode(
                        token,
                        getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
                        algorithms=[getattr(settings, "JWT_ALGORITHM", "HS256")],
                    )
                    user = await database_sync_to_async(get_user_model().objects.get)(id=payload.get("user_id"))
                    scope["user"] = user
                except Exception:
                    scope["user"] = AnonymousUser()
            else:
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


class WebSocketRateLimitMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        user = scope.get("user")
        ip = scope.get("client", [None])[0]
        identifier = f"user:{getattr(user, 'id', 'anon')}|ip:{ip}"
        limit = int(getattr(settings, "WS_CONNECTION_LIMIT", 5))
        key = f"wsconn:{identifier}"
        count = cache.get(key, 0)
        if count >= limit:
            await send({"type": "websocket.close"})
            return
        cache.set(key, count + 1, timeout=60)
        try:
            return await super().__call__(scope, receive, send)
        finally:
            remaining = cache.get(key, 1)
            if remaining > 1:
                cache.decr(key)
            else:
                cache.delete(key)
