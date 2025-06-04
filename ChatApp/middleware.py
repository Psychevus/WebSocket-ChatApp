import json
import logging
from channels.middleware import BaseMiddleware
from django.conf import settings

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
