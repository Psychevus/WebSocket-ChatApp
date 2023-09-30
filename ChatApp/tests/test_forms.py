from django.test import TestCase
from ChatApp.models import CustomUser, Conversation
from ChatApp.forms import StartConversationForm, CustomUserCreationForm, CustomAuthenticationForm


class StartConversationFormTest(TestCase):
    def test_start_conversation_form_valid(self):
        user1 = CustomUser.objects.create_user(email="user1@example.com", password="password1")
        user2 = CustomUser.objects.create_user(email="user2@example.com", password="password2")
        Conversation.objects.create(user1=user1, user2=user2)
        data = {'participants': user2.id}
        form = StartConversationForm(data=data, request=None)
        self.assertTrue(form.is_valid())

    def test_start_conversation_form_existing_conversation(self):
        user1 = CustomUser.objects.create_user(email="user1@example.com", password="password1")
        user2 = CustomUser.objects.create_user(email="user2@example.com", password="password2")
        Conversation.objects.create(user1=user1, user2=user2)
        data = {'participants': user2.id}
        form = StartConversationForm(data=data, request=None)
        self.assertTrue(form.is_valid())


class CustomUserCreationFormTest(TestCase):
    def test_custom_user_creation_form_valid(self):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid(self):
        data = {
            'email': 'invalid-email',
            'first_name': '',
            'last_name': '',
            'password1': 'password',
            'password2': 'mismatch',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('password2', form.errors)


class CustomAuthenticationFormTest(TestCase):
    def test_custom_authentication_form_valid(self):
        user = CustomUser.objects.create_user(email="user@example.com", password="password")
        data = {'username': 'user@example.com', 'password': 'password'}
        form = CustomAuthenticationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_custom_authentication_form_invalid(self):
        data = {'username': 'user@example.com', 'password': 'wrongpassword'}
        form = CustomAuthenticationForm(data=data)
        self.assertFalse(form.is_valid())
