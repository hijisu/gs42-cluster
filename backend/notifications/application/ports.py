from typing import Protocol

from notifications.domain.notification import Notification


class Notifier(Protocol):
    """알림 채널 포트. 앱 안 알림(항상 켜짐), 웹 푸시(#60) 등이 구현한다."""

    name: str

    def send(self, notification: Notification) -> None: ...


class NotificationRepository(Protocol):
    def add(self, notification: Notification) -> Notification: ...

    def get(self, notification_id: int) -> Notification | None: ...

    def save(self, notification: Notification) -> None: ...

    def list_for_user(self, user_id: int, unread_only: bool, limit: int) -> list[Notification]: ...

    def unread_count(self, user_id: int) -> int: ...

    def mark_all_read(self, user_id: int, now) -> int: ...


class UserDirectory(Protocol):
    def ids_by_intra_ids(self, intra_ids: list[str]) -> dict[str, int]:
        """가입한 사용자만 {intra_id(소문자): user_id}로 돌려준다."""
        ...

    def staff_ids(self) -> list[int]:
        """운영팀 역할 사용자의 id."""
        ...

    def display_names(self, user_ids: list[int]) -> dict[int, str]:
        """{user_id: 표시 이름}. 이름이 없으면 intra_id."""
        ...
