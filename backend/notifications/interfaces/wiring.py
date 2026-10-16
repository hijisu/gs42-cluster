"""채널과 이벤트 구독을 조립한다(Composition Root). 새 채널(웹 푸시 등)은 channels()에 추가한다."""

from common.infrastructure.event_bus import event_bus
from notifications.application.handlers import NotificationHandlers, register_handlers
from notifications.application.service import NotificationService
from notifications.infrastructure.repositories import DjangoUserDirectory, InAppNotifier

_registered = False


def channels() -> list:
    return [InAppNotifier()]


def register() -> None:
    """프로세스당 한 번만 도메인 이벤트를 구독한다."""
    global _registered
    if _registered:
        return
    handlers = NotificationHandlers(NotificationService(channels()), DjangoUserDirectory())
    register_handlers(event_bus, handlers)
    _registered = True
