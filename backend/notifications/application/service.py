import logging
from collections.abc import Sequence

from notifications.application.ports import Notifier
from notifications.domain.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """알림을 만들어 모든 채널로 보낸다. 한 채널의 실패는 로그만 남기고 다른 채널을 막지 않는다."""

    def __init__(self, channels: Sequence[Notifier]) -> None:
        self._channels = list(channels)

    def notify(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        body: str = "",
        link: str = "",
        data: dict | None = None,
    ) -> list[str]:
        """실패한 채널 이름 목록을 돌려준다(테스트·모니터링용)."""
        notification = Notification(
            user_id=user_id, type=type, title=title, body=body, link=link, data=data or {}
        )
        failed = []
        for channel in self._channels:
            try:
                channel.send(notification)
            except Exception:
                failed.append(channel.name)
                logger.exception(
                    "알림 채널 전송 실패: channel=%s type=%s user=%s", channel.name, type, user_id
                )
        return failed
