"""푸시 구독 도메인 테스트: DB 없이 실행."""

import pytest

from notifications.domain.push import (
    InvalidSubscription,
    PushSubscription,
    validate_endpoint,
    validate_key,
)

GOOD = [
    "https://fcm.googleapis.com/fcm/send/abc:123",
    "https://updates.push.services.mozilla.com/wpush/v2/gAAAA",
    "https://web.push.apple.com/QGxyz",
    "https://wns2-par02p.notify.windows.com/w/?token=abc",
]


@pytest.mark.parametrize("endpoint", GOOD)
def test_known_push_services_are_accepted(endpoint):
    assert validate_endpoint(endpoint) == endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "http://fcm.googleapis.com/fcm/send/abc",  # https 아님
        "https://169.254.169.254/latest/meta-data/",  # 클라우드 메타데이터(SSRF)
        "https://localhost/push",
        "https://127.0.0.1/push",
        "https://internal.example.com/push",
        "https://evil.com/?x=fcm.googleapis.com",  # 호스트가 아닌 곳에만 있는 이름
        "https://fcm.googleapis.com.evil.com/push",  # 접미사 위조
        "https://evilgoogleapis.com/push",  # '.' 없이 이어붙인 접미사
        "https://user:pw@fcm.googleapis.com/push",  # 자격 증명 포함
        "https://fcm.googleapis.com:8443/push",  # 비표준 포트
        "ftp://fcm.googleapis.com/push",
        "https://fcm.googleapis.com/" + "a" * 2000,  # 너무 긺
    ],
)
def test_unsafe_or_unknown_endpoints_are_rejected(endpoint):
    with pytest.raises(InvalidSubscription):
        validate_endpoint(endpoint)


def test_explicit_default_port_is_fine():
    validate_endpoint("https://fcm.googleapis.com:443/fcm/send/abc")


@pytest.mark.parametrize("value", ["", "has space", "a/b+c", "x" * 513, "한글"])
def test_invalid_keys_are_rejected(value):
    with pytest.raises(InvalidSubscription):
        validate_key(value, "auth")


def test_base64url_keys_are_accepted():
    assert validate_key("BEl62iUYgUivxIkv69yViEuiBIa-Ib9_", "p256dh")


def test_create_validates_everything():
    sub = PushSubscription.create(1, GOOD[0], "BEl62iUYgUivxIkv", "tBHItJI5svbpez7K")
    assert (sub.user_id, sub.endpoint) == (1, GOOD[0])
    with pytest.raises(InvalidSubscription):
        PushSubscription.create(1, "https://evil.com/x", "BEl62iUYgUivxIkv", "tBHItJI5svbpez7K")
    with pytest.raises(InvalidSubscription):
        PushSubscription.create(1, GOOD[0], "bad key!", "tBHItJI5svbpez7K")
