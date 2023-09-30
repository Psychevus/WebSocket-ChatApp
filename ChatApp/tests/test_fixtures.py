from django.test import TestCase
from ChatApp.models import CustomUser


class CustomUserFixtureTestCase(TestCase):
    fixtures = ['ChatApp/tests/fixture.json']

    def test_user_count(self):
        users_count = CustomUser.objects.count()
        self.assertEqual(users_count, 2)
