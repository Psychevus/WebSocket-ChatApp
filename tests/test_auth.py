import pytest
from django.urls import reverse
from ChatApp.models import CustomUser

@pytest.mark.django_db
def test_user_login(client):
    user = CustomUser.objects.create_user(email="user@example.com", password="pass")
    assert client.login(username="user@example.com", password="pass")
    assert str(user.pk) == client.session.get('_auth_user_id')


@pytest.mark.django_db
def test_login_view_success(client):
    user = CustomUser.objects.create_user(email="view@example.com", password="pass")
    resp = client.post(reverse("chat:login"), {"username": user.email, "password": "pass"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(reverse("chat:conversations_list"))
