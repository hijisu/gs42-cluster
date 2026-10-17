import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def logged_in_client(settings):
    settings.MOCK_LOGIN_ENABLED = True
    client = Client(enforce_csrf_checks=True)
    client.post("/api/auth/mock-login", {"role": "student"}, content_type="application/json")
    client.get("/api/auth/me")  # CSRF 쿠키 발급
    return client


def post(settings, origin):
    client = logged_in_client(settings)
    token = client.cookies["csrftoken"].value
    return client.post(
        "/api/auth/logout",
        HTTP_ORIGIN=origin,
        HTTP_X_CSRFTOKEN=token,
        content_type="application/json",
        data="{}",
    )


@pytest.mark.parametrize(
    "origin", ["http://192.168.0.7:5173", "http://10.143.2.186:5173", "http://172.16.3.4:5173"]
)
def test_debug_trusts_private_network_frontends(settings, origin):
    settings.DEBUG = True
    assert post(settings, origin).status_code == 204


@pytest.mark.parametrize(
    "origin",
    ["https://evil.example.com", "http://8.8.8.8:5173", "http://192.168.0.7.evil.com", "null"],
)
def test_debug_still_rejects_public_origins(settings, origin):
    settings.DEBUG = True
    assert post(settings, origin).status_code == 403


def test_production_never_trusts_private_ips(settings):
    settings.DEBUG = False
    assert post(settings, "http://192.168.0.7:5173").status_code == 403
