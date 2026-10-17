import io
import json

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
