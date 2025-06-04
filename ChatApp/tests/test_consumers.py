import json
import pytest
from channels.testing import WebsocketCommunicator
from WebSocketChatApp.routing import application
from ChatApp.models import CustomUser, Conversation, Message

@pytest.mark.asyncio
async def test_message_persistence(db):
    user1 = CustomUser.objects.create_user(email="cuser1@example.com", password="pass")
    user2 = CustomUser.objects.create_user(email="cuser2@example.com", password="pass")
    conversation = Conversation.objects.create(user1=user1, user2=user2)

    communicator = WebsocketCommunicator(application, f"ws/chat/{conversation.id}/")
    communicator.scope['user'] = user1

    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({'message': 'hello'})
    response = await communicator.receive_json_from()
    assert response['message'] == 'hello'

    await communicator.disconnect()

    assert Message.objects.filter(conversation=conversation, sender=user1, content='hello').exists()
