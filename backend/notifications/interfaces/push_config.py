"""VAPID 설정 로드. 잘못된 설정이어도 서버는 뜨고 푸시만 꺼진다."""

import logging
from dataclasses import dataclass

from django.conf import settings

from notifications.infrastructure.vapid import public_key_of

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PushConfig:
    public_key: str  # 개인키에서 계산한 값(서명에 쓰이는 키와 항상 일치)
    private_key: str
    subject: str


def load_push_config() -> PushConfig | None:
    private = settings.VAPID_PRIVATE_KEY
    if not private:
        return None
    try:
        derived = public_key_of(private)
    except Exception:
        logger.error(
            "VAPID_PRIVATE_KEY 형식이 올바르지 않아 웹 푸시를 끕니다 "
            "(manage.py generate_vapid_keys 로 새로 만드세요)"
        )
        return None
    configured = settings.VAPID_PUBLIC_KEY
    if configured and configured != derived:
        logger.warning(
            "VAPID_PUBLIC_KEY 가 VAPID_PRIVATE_KEY 와 짝이 아닙니다. "
            "개인키에서 계산한 공개키를 사용합니다"
        )
    return PushConfig(public_key=derived, private_key=private, subject=settings.VAPID_SUBJECT)
