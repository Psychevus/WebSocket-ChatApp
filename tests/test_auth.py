import pytest
from ChatApp.models import CustomUser

@pytest.mark.django_db
def test_user_login(client):
    user = CustomUser.objects.create_user(email="user@example.com", password="pass")
    assert client.login(username="user@example.com", password="pass")
    assert str(user.pk) == client.session.get('_auth_user_id')
