from django.test import TestCase

from ChatApp.models import CustomUser, Conversation


class CustomUserModelTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpassword",
            first_name="John",
            last_name="Doe",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)


class ConversationModelTestCase(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            password="user1password",
        )
        self.user2 = CustomUser.objects.create_user(
            email="user2@example.com",
            password="user2password",
        )
        self.conversation = Conversation.objects.create(user1=self.user1, user2=self.user2)

    def test_get_participants(self):
        participants = self.conversation.get_participants()
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)
