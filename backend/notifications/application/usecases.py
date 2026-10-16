from dataclasses import dataclass
from datetime import datetime

from notifications.application.ports import NotificationRepository
from notifications.domain.errors import NotificationNotFound
from notifications.domain.notification import Notification

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


@dataclass(frozen=True)
class NotificationList:
    items: list[Notification]
    unread_count: int


class ListNotificationsUseCase:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    def execute(
        self, user_id: int, unread_only: bool = False, limit: int = DEFAULT_LIMIT
    ) -> NotificationList:
        limit = max(1, min(limit, MAX_LIMIT))
        return NotificationList(
            items=self._repo.list_for_user(user_id, unread_only, limit),
            unread_count=self._repo.unread_count(user_id),
        )


class MarkReadUseCase:
    def __init__(self, repo: NotificationRepository, clock) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, notification_id: int, user_id: int) -> Notification:
        notification = self._repo.get(notification_id)
        # 남의 알림은 존재 여부도 알려 주지 않는다.
        if notification is None or notification.user_id != user_id:
            raise NotificationNotFound("알림을 찾을 수 없습니다")
        notification.mark_read(self._clock())
        self._repo.save(notification)
        return notification


class MarkAllReadUseCase:
    def __init__(self, repo: NotificationRepository, clock) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, user_id: int) -> int:
        now: datetime = self._clock()
        return self._repo.mark_all_read(user_id, now)
