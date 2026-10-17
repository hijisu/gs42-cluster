"""웹 푸시 구독. 순수 파이썬(Django 의존 없음)."""

import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

from common.domain.errors import InvalidRequestError

# 서버가 구독 endpoint 로 직접 요청을 보내므로(SSRF 방지)
# https 이고 알려진 푸시 서비스 호스트만 허용한다.
# Chrome/Edge/Samsung: FCM, Firefox: Mozilla autopush, Safari/iOS: Apple, Edge(Windows): WNS.
# googleapis.com 전체가 아니라 FCM 호스트만 허용한다(다른 하위 도메인은 사용자가 만들 수 있다).
ALLOWED_PUSH_HOSTS = ("fcm.googleapis.com",)
ALLOWED_PUSH_HOST_SUFFIXES = (
    ".push.services.mozilla.com",  # updates.push.services.mozilla.com
    ".push.apple.com",  # web.push.apple.com
    ".notify.windows.com",  # *.notify.windows.com
)
MAX_ENDPOINT_LENGTH = 2000
_BASE64URL = re.compile(r"^[A-Za-z0-9_\-]+={0,2}$")


class InvalidSubscription(InvalidRequestError):
    code = "invalid_subscription"


def validate_endpoint(endpoint: str) -> str:
    if not endpoint or len(endpoint) > MAX_ENDPOINT_LENGTH:
        raise InvalidSubscription("구독 endpoint가 올바르지 않습니다")
    # 푸시 서비스 주소는 ASCII 이고 공백·제어문자가 없다(호스트 위장·요청 분할 방지).
    if not endpoint.isascii() or any(ord(ch) <= 0x20 or ord(ch) == 0x7F for ch in endpoint):
        raise InvalidSubscription("구독 endpoint가 올바르지 않습니다")
    try:
        # urlsplit 과 .port 는 잘못된 주소(숫자가 아닌 포트, 65535 초과, 닫히지 않은 [ 등)에
        # ValueError 를 던지므로 400 으로 바꾼다.
        parts = urlsplit(endpoint)
        host = (parts.hostname or "").lower()
        port = parts.port
    except ValueError as exc:
        raise InvalidSubscription("구독 endpoint가 올바르지 않습니다") from exc
    if parts.scheme != "https" or parts.username or parts.password or port not in (None, 443):
        raise InvalidSubscription("푸시 endpoint는 https 주소여야 합니다")
    if host not in ALLOWED_PUSH_HOSTS and not host.endswith(ALLOWED_PUSH_HOST_SUFFIXES):
        raise InvalidSubscription("지원하지 않는 푸시 서비스입니다")
    return endpoint


def validate_key(value: str, name: str) -> str:
    if not value or len(value) > 512 or not _BASE64URL.match(value):
        raise InvalidSubscription(f"구독 키({name})가 올바르지 않습니다")
    return value


@dataclass
class PushSubscription:
    user_id: int
    endpoint: str
    p256dh: str
    auth: str
    id: int | None = None
    created_at: datetime | None = None

    @classmethod
    def create(cls, user_id: int, endpoint: str, p256dh: str, auth: str) -> "PushSubscription":
        return cls(
            user_id=user_id,
            endpoint=validate_endpoint(endpoint),
            p256dh=validate_key(p256dh, "p256dh"),
            auth=validate_key(auth, "auth"),
        )
