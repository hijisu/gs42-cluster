"""알림 엔티티. 순수 파이썬(Django 의존 없음)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class NotificationType(StrEnum):
    """알림 종류 코드.

    표시 문구는 프론트가 이 코드로 매핑한다. title/body는 푸시 등 서버 채널용 기본 문구다.
    """

    MEETING_CONFIRMED = "meeting_confirmed"
    MEETING_PROPOSED = "meeting_proposed"
    RESERVATION_APPROVED = "reservation_approved"
    RESERVATION_REJECTED = "reservation_rejected"
    RESERVATION_REASSIGNED = "reservation_reassigned"
    REVIEW_REQUESTED = "review_requested"


@dataclass
class Notification:
    user_id: int
    type: NotificationType
    title: str
    body: str = ""
    link: str = ""
    data: dict = field(default_factory=dict)
    created_at: datetime | None = None
    read_at: datetime | None = None
    id: int | None = None

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self, now: datetime) -> None:
        """이미 읽은 알림이면 처음 읽은 시각을 유지한다(멱등)."""
        if self.read_at is None:
            self.read_at = now
