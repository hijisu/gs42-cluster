"""웹 푸시 구독. 순수 파이썬(Django 의존 없음)."""

import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

from common.domain.errors import InvalidRequestError

# 서버가 구독 endpoint 로 직접 요청을 보내므로(SSRF 방지)
# https 이고 알려진 푸시 서비스 호스트만 허용한다.
# Chrome/Edge/Samsung: FCM, Firefox: Mozilla autopush, Safari/iOS: Apple, Edge(Windows): WNS.
ALLOWED_PUSH_HOST_SUFFIXES = (
    ".googleapis.com",  # fcm.googleapis.com
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
    parts = urlsplit(endpoint)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443):
        raise InvalidSubscription("푸시 endpoint는 https 주소여야 합니다")
    if not any(host.endswith(suffix) for suffix in ALLOWED_PUSH_HOST_SUFFIXES):
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
