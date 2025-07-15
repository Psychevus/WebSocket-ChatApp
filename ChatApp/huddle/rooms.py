# pragma: no cover
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

@dataclass
class HuddleRoom:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    router_rtp_capabilities: dict = field(default_factory=lambda: {
        "codecs": [
            {"kind": "audio", "mimeType": "audio/opus", "clockRate": 48000, "channels": 2},
            {"kind": "video", "mimeType": "video/VP8", "clockRate": 90000},
        ],
        "headerExtensions": [],
    })

_rooms: dict[str, HuddleRoom] = {}


def create_room() -> HuddleRoom:
    room = HuddleRoom()
    _rooms[room.id] = room
    return room
