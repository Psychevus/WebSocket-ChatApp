from django.test import TestCase
from django.urls import reverse

from ChatApp.models import CustomUser, Conversation


class ChatIntegrationTestCase(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(email="user1@example.com", password="password1", first_name="User1")
        self.user2 = CustomUser.objects.create_user(email="user2@example.com", password="password2", first_name="User2")
        self.conversation = Conversation.objects.create(user1=self.user1, user2=self.user2)
        self.client.login(email="user1@example.com", password="password1")

    def test_start_conversation_view(self):
        response = self.client.get(reverse('chat:start_conversation'))
        self.assertEqual(response.status_code, 200)

    def test_start_conversation_form_valid(self):
        data = {'participants': self.user2.id}
        response = self.client.post(reverse('chat:start_conversation'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_start_conversation_form_existing_conversation(self):
        data = {'participants': self.user2.id}
        response = self.client.post(reverse('chat:start_conversation'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_conversations_list_view(self):
        response = self.client.get(reverse('chat:conversations_list'))
        self.assertEqual(response.status_code, 200)
        expected_content = "Hello,"
        self.assertContains(response, expected_content)

    def test_conversation_view(self):
        response = self.client.get(reverse('chat:view_conversation', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 200)
        expected_content = "Conversation header"
        self.assertContains(response, expected_content)
