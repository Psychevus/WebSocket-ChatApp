from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, ChatRoom


class ChatRoomWebSocketTests(TransactionTestCase):
    def test_room_message_exchange(self):
        user1 = CustomUser.objects.create_user(email="r1@example.com", password="pass")
        user2 = CustomUser.objects.create_user(email="r2@example.com", password="pass")
        room = ChatRoom.objects.create(name="Test")
        room.members.add(user1, user2)

        async def inner():
            comm1 = WebsocketCommunicator(application, f"ws/rooms/{room.id}/")
            comm1.scope["user"] = user1
            comm2 = WebsocketCommunicator(application, f"ws/rooms/{room.id}/")
            comm2.scope["user"] = user2

            connected, _ = await comm1.connect()
            assert connected
            connected, _ = await comm2.connect()
            assert connected

            await comm1.send_json_to({"message": "hi"})
            resp = await comm2.receive_json_from()
            assert resp["message"] == "hi"

            await comm1.disconnect()
            await comm2.disconnect()

        async_to_sync(inner)()
