import io
import json
import urllib.error

import pytest

from accounts.domain.errors import AuthenticationFailed
from accounts.infrastructure.fortytwo import ME_URL, TOKEN_URL, FortyTwoOAuthClient


def test_oauth_requests_identify_service_to_avoid_upstream_403(monkeypatch):
    requests = []

    def urlopen(request, timeout):
        requests.append(request)
        # 42 rejects the default Python urllib User-Agent.
        assert request.get_header("User-agent") == "gs42-cluster/1.0"
        assert request.get_header("Accept") == "application/json"
        if request.full_url == TOKEN_URL:
            assert request.method == "POST"
            body = {"access_token": "test-token"}
        else:
            assert request.full_url == ME_URL
            assert request.get_header("Authorization") == "Bearer test-token"
            body = {"login": "alice", "usual_full_name": "Alice", "staff?": False}
        return io.BytesIO(json.dumps(body).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    client = FortyTwoOAuthClient("uid", "secret", "http://localhost:5173/api/auth/callback")

    profile = client.fetch_profile("code")

    assert profile.intra_id == "alice"
    assert len(requests) == 2


def _failing_client(monkeypatch, exc_for):
    def urlopen(request, timeout):
        stage = "token" if request.full_url == TOKEN_URL else "profile"
        if (outcome := exc_for(stage)) is None:
            body = {"access_token": "t"} if stage == "token" else {"login": "a"}
            return io.BytesIO(json.dumps(body).encode())
        if isinstance(outcome, bytes):
            return io.BytesIO(outcome)
        raise outcome

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return FortyTwoOAuthClient("uid", "super-secret", "http://localhost/cb")


def _failure(client):
    with pytest.raises(AuthenticationFailed) as info:
        client.fetch_profile("one-time-code")
    return info.value


def _http(status):
    return urllib.error.HTTPError("https://x", status, "msg", {}, io.BytesIO(b"secret-body"))


@pytest.mark.parametrize(
    ("outcome", "status", "reason"),
    [
        (_http(403), 403, "http_error"),
        (_http(401), 401, "http_error"),
        (urllib.error.URLError("dns"), None, "network_error"),
        (TimeoutError(), None, "timeout"),
        (b"<html>not json</html>", None, "invalid_response"),
        (b'{"no_token": 1}', None, "invalid_response"),
    ],
)
def test_token_failure_reports_stage_status_and_reason(monkeypatch, outcome, status, reason):
    error = _failure(_failing_client(monkeypatch, lambda stage: outcome))
    assert (error.stage, error.status, error.reason) == ("token", status, reason)


def test_profile_failure_is_distinguished_from_token_failure(monkeypatch):
    client = _failing_client(monkeypatch, lambda s: _http(500) if s == "profile" else None)
    error = _failure(client)
    assert (error.stage, error.status) == ("profile", 500)


def test_profile_without_login_reports_missing_login(monkeypatch):
    client = _failing_client(monkeypatch, lambda s: b"{}" if s == "profile" else None)
    error = _failure(client)
    assert (error.stage, error.reason) == ("profile", "missing_login")


def test_failure_details_never_contain_secrets_or_response_body(monkeypatch):
    error = _failure(_failing_client(monkeypatch, lambda stage: _http(403)))
    text = f"{error} {error.stage} {error.status} {error.reason}"
    for secret in ("super-secret", "one-time-code", "secret-body"):
        assert secret not in text


@pytest.mark.parametrize(
    "image, expected",
    [
        ({"link": "https://cdn.example/photo.jpg"}, "https://cdn.example/photo.jpg"),
        (
            {"link": None, "versions": {"medium": "https://cdn.example/medium.jpg"}},
            "https://cdn.example/medium.jpg",
        ),
        (None, ""),
        ({"link": "javascript:alert(1)"}, ""),
        # 형식이 달라도(문자열·숫자·잘못된 versions) 로그인이 실패하지 않고 사진만 비운다.
        ("https://cdn.example/legacy.jpg", ""),
        ({"link": 12345}, ""),
        ({"link": None, "versions": "medium"}, ""),
        ({"link": "http://cdn.example/insecure.jpg"}, ""),
    ],
)
def test_profile_photo_extraction(monkeypatch, image, expected):
    client = FortyTwoOAuthClient("uid", "secret", "http://localhost/callback")
    monkeypatch.setattr(client, "_post_token", lambda code: "token")
    monkeypatch.setattr(client, "_get_json", lambda url, token: {"login": "alice", "image": image})
    assert client.fetch_profile("code").image_url == expected
