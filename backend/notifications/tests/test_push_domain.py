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
        "https://storage.googleapis.com/bucket/push",  # googleapis.com 의 다른 서비스
        "https://my-bucket.storage.googleapis.com/",  # 누구나 만들 수 있는 하위 도메인
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


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com:443/fcm/send/abc",  # 명시한 기본 포트
        "https://fcm.googleapis.com:/fcm/send/abc",  # 빈 포트 = 기본 포트(RFC 3986)
        "https://FCM.GoogleAPIs.com/fcm/send/abc",  # 호스트는 대소문자 무관
    ],
)
def test_default_port_forms_and_case_are_fine(endpoint):
    assert validate_endpoint(endpoint) == endpoint


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


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com:abc/push",  # 포트가 숫자가 아님 (bug #85)
        "https://fcm.googleapis.com:65536/push",  # 포트 범위 초과 (bug #85)
        "https://[broken/push",  # 닫히지 않은 IPv6 괄호 (bug #85)
        "https://fcm.googleapis.com:-1/push",
        "https://[::1/push",
        "https://[fe80::1%25eth0]/push",
        "https://\x00fcm.googleapis.com/push",
        "https://fcm.googleapis.com\n.evil.com/push",
        "https:///fcm.googleapis.com/push",
        "https://",
        "https:",
        "//fcm.googleapis.com/push",
        "fcm.googleapis.com/push",
        "https://fcm.googleapis.com\\@evil.com/push",
        "https://ﬁcm.googleapis.com/push",  # 유니코드 합자
    ],
)
def test_malformed_endpoints_raise_invalid_subscription_never_a_raw_error(endpoint):
    """잘못된 주소가 ValueError 등으로 새어 나가 API 500 이 되면 안 된다."""
    with pytest.raises(InvalidSubscription):
        validate_endpoint(endpoint)


def test_random_garbage_only_ever_raises_invalid_subscription():
    """결정적 퍼징: 어떤 입력이든 통과(문자열 반환)하거나 InvalidSubscription 이어야 한다."""
    import random

    rng = random.Random(42)
    pieces = [
        "https://",
        "http://",
        "fcm.googleapis.com",
        ".push.apple.com",
        ":",
        "443",
        "99999",
        "[",
        "]",
        "@",
        "/",
        "?",
        "#",
        "%",
        "\\",
        "\x00",
        " ",
        "..",
        "한글",
        "::1",
        "-",
        "_",
    ]
    for _ in range(3000):
        candidate = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 8)))
        try:
            result = validate_endpoint(candidate)
        except InvalidSubscription:
            continue
        assert result == candidate  # 통과했다면 원문 그대로여야 한다
