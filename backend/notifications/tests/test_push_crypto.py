"""전송기가 만든 요청이 실제 푸시 규격(RFC 8291 암호화 + RFC 8292 VAPID)에 맞는지 검증한다.

로컬 HTTP 서버가 푸시 서비스 역할을 하고, 구독자(브라우저) 키쌍으로 본문을 복호화하며
Authorization 의 VAPID JWT 를 서버 공개키로 검증한다. DB 는 쓰지 않는다.
"""

import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import http_ece
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid

from notifications.application.push import SubscriptionGone
from notifications.domain.push import PushSubscription
from notifications.infrastructure.push import PyWebPushSender
from notifications.infrastructure.vapid import generate_keys, public_key_of


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class Browser:
    """푸시 구독자(브라우저) 키쌍."""

    def __init__(self):
        self.private = ec.generate_private_key(ec.SECP256R1())
        point = self.private.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        self.p256dh = b64(point)
        self.auth_secret = os.urandom(16)
        self.auth = b64(self.auth_secret)

    def decrypt(self, body: bytes) -> dict:
        plain = http_ece.decrypt(
            body, private_key=self.private, auth_secret=self.auth_secret, version="aes128gcm"
        )
        return json.loads(plain.decode())


@pytest.fixture
def push_service():
    """로컬 가짜 푸시 서비스. 응답 상태는 service.status 로 바꾼다."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            self.server.requests.append(
                {
                    "path": self.path,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "body": self.rfile.read(length),
                }
            )
            self.send_response(self.server.status)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.requests = []
    server.status = 201
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.endpoint = f"http://127.0.0.1:{server.server_port}/push/abc"
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def keys():
    public, private = generate_keys()
    return public, private


def make_sender(private):
    return PyWebPushSender(private, "mailto:admin@example.com", timeout=5)


def test_generated_keys_are_a_matching_pair_in_browser_format():
    public, private = generate_keys()
    assert public_key_of(private) == public
    assert len(unb64(public)) == 65 and unb64(public)[0] == 4  # 비압축 P-256 점
    assert len(unb64(private)) == 32
    assert "=" not in public and "=" not in private  # base64url, 패딩 없음


def test_each_generation_is_different():
    assert generate_keys() != generate_keys()


def test_payload_is_encrypted_so_only_the_subscriber_can_read_it(push_service, keys):
    browser = Browser()
    sub = PushSubscription(1, push_service.endpoint, browser.p256dh, browser.auth)
    payload = {
        "title": "면담이 확정되었어요",
        "body": "10.20 14:00 · 1층",
        "link": "/meeting",
        "type": "meeting_confirmed",
    }
    make_sender(keys[1]).send(sub, payload)

    (request,) = push_service.requests
    assert request["path"] == "/push/abc"
    assert request["headers"]["content-encoding"] == "aes128gcm"
    assert "면담이 확정되었어요".encode() not in request["body"]  # 평문이 아니다
    assert browser.decrypt(request["body"]) == payload  # 구독자 키로만 복호화된다


def test_another_browsers_key_cannot_decrypt(push_service, keys):
    owner, stranger = Browser(), Browser()
    sub = PushSubscription(1, push_service.endpoint, owner.p256dh, owner.auth)
    make_sender(keys[1]).send(sub, {"title": "비공개", "body": "", "link": "/", "type": "x"})
    with pytest.raises(Exception):  # noqa: B017  (복호화 실패 예외 종류는 라이브러리 내부)
        stranger.decrypt(push_service.requests[0]["body"])


def test_vapid_signature_verifies_with_the_public_key_we_hand_to_browsers(push_service, keys):
    public, private = keys
    browser = Browser()
    make_sender(private).send(
        PushSubscription(1, push_service.endpoint, browser.p256dh, browser.auth),
        {"title": "t", "body": "", "link": "/", "type": "x"},
    )
    auth = push_service.requests[0]["headers"]["authorization"]
    assert auth.startswith("vapid ")
    fields = dict(part.strip().split("=", 1) for part in auth[len("vapid ") :].split(","))
    assert fields["k"] == public  # 브라우저가 구독 때 쓴 applicationServerKey 와 같은 키

    signed, signature = fields["t"].rsplit(".", 1)
    assert Vapid.from_raw_public(public.encode()).verify_token(
        validation_token=signed.encode(), verification_token=signature
    )
    claims = json.loads(unb64(signed.split(".")[1]))
    assert claims["sub"] == "mailto:admin@example.com"
    assert claims["aud"] == f"http://127.0.0.1:{push_service.server_port}"  # 푸시 서비스 origin


def test_signature_from_another_server_key_does_not_verify(push_service, keys):
    browser = Browser()
    make_sender(keys[1]).send(
        PushSubscription(1, push_service.endpoint, browser.p256dh, browser.auth),
        {"title": "t", "body": "", "link": "/", "type": "x"},
    )
    auth = push_service.requests[0]["headers"]["authorization"]
    fields = dict(part.strip().split("=", 1) for part in auth[len("vapid ") :].split(","))
    signed, signature = fields["t"].rsplit(".", 1)
    other_public, _ = generate_keys()
    assert not Vapid.from_raw_public(other_public.encode()).verify_token(
        validation_token=signed.encode(), verification_token=signature
    )


@pytest.mark.parametrize("status", [404, 410])
def test_expired_subscription_is_reported_as_gone(push_service, keys, status):
    push_service.status = status
    browser = Browser()
    sub = PushSubscription(1, push_service.endpoint, browser.p256dh, browser.auth)
    with pytest.raises(SubscriptionGone):
        make_sender(keys[1]).send(sub, {"title": "t", "body": "", "link": "/", "type": "x"})


@pytest.mark.parametrize("status", [400, 401, 413, 429, 500, 503])
def test_other_failures_are_not_treated_as_gone(push_service, keys, status):
    push_service.status = status
    browser = Browser()
    sub = PushSubscription(1, push_service.endpoint, browser.p256dh, browser.auth)
    with pytest.raises(Exception) as info:  # noqa: B017
        make_sender(keys[1]).send(sub, {"title": "t", "body": "", "link": "/", "type": "x"})
    assert not isinstance(info.value, SubscriptionGone)
