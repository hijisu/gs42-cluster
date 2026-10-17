import pytest
from django.test import Client
from rest_framework.test import APIClient

from accounts.application.ports import FortyTwoProfile
from accounts.domain.errors import AuthenticationFailed
from accounts.interfaces import deps

pytestmark = pytest.mark.django_db


def mock_login(client, role):
    return client.post("/api/auth/mock-login", {"role": role}, format="json")


def test_mock_login_issues_session_and_me_returns_role():
    client = APIClient()
    assert mock_login(client, "student").status_code == 200
    body = client.get("/api/auth/me").json()
    assert body["intra_id"] == "student" and body["role"] == "student"


def test_me_requires_login_with_401():
    assert APIClient().get("/api/auth/me").status_code == 401


def test_student_gets_403_on_staff_api():
    client = APIClient()
    mock_login(client, "student")
    assert client.get("/api/staff/ping").status_code == 403


def test_staff_can_access_staff_api():
    client = APIClient()
    mock_login(client, "staff")
    assert client.get("/api/staff/ping").status_code == 200


def test_anonymous_gets_401_on_staff_api():
    assert APIClient().get("/api/staff/ping").status_code == 401


def test_mock_login_blocked_when_disabled(settings):
    settings.MOCK_LOGIN_ENABLED = False
    assert mock_login(APIClient(), "staff").status_code == 404


def test_mock_login_rejects_unknown_role():
    assert mock_login(APIClient(), "admin").status_code == 400


def test_logout_requires_csrf_and_clears_session():
    client = APIClient(enforce_csrf_checks=True)
    client.post("/api/auth/mock-login", {"role": "student"}, format="json")
    token = client.get("/api/auth/me").cookies["csrftoken"].value
    assert client.post("/api/auth/logout").status_code == 403
    assert client.post("/api/auth/logout", HTTP_X_CSRFTOKEN=token).status_code == 204
    assert client.get("/api/auth/me").status_code == 401


class FakeFortyTwo:
    def __init__(self, profile=None, error=False):
        self.profile, self.error = profile, error

    def authorize_url(self, state):
        return f"https://intra.example/authorize?state={state}"

    def fetch_profile(self, code):
        if self.error:
            raise AuthenticationFailed("boom", stage="token", status=403, reason="http_error")
        return self.profile


def test_login_redirects_to_42_with_state(settings, monkeypatch):
    settings.FORTYTWO_UID = "uid"
    monkeypatch.setattr(deps, "fortytwo_client", lambda: FakeFortyTwo())
    response = Client().get("/api/auth/login")
    assert response.status_code == 302
    assert "state=" in response["Location"]


def test_login_without_oauth_config_returns_503(settings):
    settings.FORTYTWO_UID = ""
    response = Client().get("/api/auth/login")
    assert response.status_code == 503 and response.json() == {"code": "oauth_not_configured"}


def _login_flow(settings, monkeypatch, fake, state_ok=True):
    settings.FORTYTWO_UID = "uid"
    monkeypatch.setattr(deps, "fortytwo_client", lambda: fake)
    client = Client()
    state = client.get("/api/auth/login")["Location"].split("state=")[1]
    return client, client.get(
        "/api/auth/callback", {"code": "c", "state": state if state_ok else "wrong"}
    )


def test_callback_creates_user_and_staff_ids_decide_role(settings, monkeypatch):
    settings.STAFF_INTRA_IDS = ["alice"]
    client, response = _login_flow(
        settings,
        monkeypatch,
        FakeFortyTwo(FortyTwoProfile("alice", "Alice", image_url="https://cdn.example/alice.jpg")),
    )
    assert response.status_code == 302 and response["Location"].endswith("/")
    me = APIClient()
    me.cookies = client.cookies
    payload = me.get("/api/auth/me").json()
    assert payload["role"] == "staff"
    assert payload["image_url"] == "https://cdn.example/alice.jpg"


def test_callback_rejects_state_mismatch(settings, monkeypatch):
    _, response = _login_flow(
        settings, monkeypatch, FakeFortyTwo(FortyTwoProfile("bob", "Bob")), state_ok=False
    )
    assert response["Location"].endswith("/login?error=invalid_state")


def test_callback_handles_42_failure(settings, monkeypatch):
    _, response = _login_flow(settings, monkeypatch, FakeFortyTwo(error=True))
    assert response["Location"].endswith("/login?error=auth_failed")


def test_callback_logs_failure_diagnosis_without_secrets(settings, monkeypatch, caplog):
    settings.FORTYTWO_UID = "uid"
    settings.FORTYTWO_SECRET = "super-secret"
    with caplog.at_level("WARNING", logger="accounts.interfaces.views"):
        _login_flow(settings, monkeypatch, FakeFortyTwo(error=True))
    [record] = [r for r in caplog.records if r.name == "accounts.interfaces.views"]
    message = record.getMessage()
    assert "stage=token" in message and "status=403" in message and "reason=http_error" in message
    assert "super-secret" not in message and "code=c" not in message


def test_state_mismatch_does_not_log_oauth_failure(settings, monkeypatch, caplog):
    with caplog.at_level("WARNING", logger="accounts.interfaces.views"):
        _login_flow(settings, monkeypatch, FakeFortyTwo(), state_ok=False)
    assert not [r for r in caplog.records if r.name == "accounts.interfaces.views"]
