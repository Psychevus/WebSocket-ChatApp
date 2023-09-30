import json
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from ChatApp.models import Conversation

CustomUser = get_user_model()


class ChatViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            password="user1password",
        )
        self.user2 = CustomUser.objects.create_user(
            email="user2@example.com",
            password="user2password",
        )
        self.conversation = Conversation.objects.create(user1=self.user1, user2=self.user2)
        self.client.login(username="user1@example.com", password="user1password")

    def test_register_view(self):
        response = self.client.get(reverse('chat:register'))
        self.assertEqual(response.status_code, 200)

        data = {
            'email': 'newuser@example.com',
            'password1': 'newuserpassword',
            'password2': 'newuserpassword',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = self.client.post(reverse('chat:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.filter(email='newuser@example.com').count(), 1)

    def test_user_login_view(self):
        response = self.client.get(reverse('chat:login'))
        self.assertEqual(response.status_code, 200)

        data = {
            'username': 'user1@example.com',
            'password': 'user1password',
        }
        response = self.client.post(reverse('chat:login'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('chat:conversations_list'))

    def test_user_logout_view(self):
        response = self.client.get(reverse('chat:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('chat:login'))

    def test_conversations_list_view(self):
        response = self.client.get(reverse('chat:conversations_list'))
        self.assertEqual(response.status_code, 200)

    def test_conversation_view(self):
        response = self.client.get(reverse('chat:view_conversation', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 200)
        expected_content = "Conversation header"
        self.assertContains(response, expected_content)

    def test_start_conversation_view(self):
        response = self.client.get(reverse('chat:start_conversation'))
        self.assertEqual(response.status_code, 200)
        data = {'participants': self.user2.id}
        response = self.client.post(reverse('chat:start_conversation'), data=data)
        self.assertEqual(response.status_code, 302)
        conversation_id = Conversation.objects.latest('id').id
        expected_url = reverse('chat:view_conversation', args=[conversation_id])
        self.assertRedirects(response, expected_url)

    def test_search_users_view(self):
        response = self.client.get(reverse('chat:search_users') + '?q=user2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data), 1)
