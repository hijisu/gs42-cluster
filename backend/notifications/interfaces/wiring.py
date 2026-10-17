"""채널과 이벤트 구독을 조립한다(Composition Root). 새 채널(웹 푸시 등)은 channels()에 추가한다."""

from common.infrastructure.event_bus import event_bus
from notifications.application.handlers import NotificationHandlers, register_handlers
from notifications.application.push import WebPushNotifier
from notifications.application.service import NotificationService
from notifications.infrastructure.push import DjangoPushSubscriptionRepository, PyWebPushSender
from notifications.infrastructure.repositories import DjangoUserDirectory, InAppNotifier
from notifications.interfaces.push_config import load_push_config

_registered = False


def channels() -> list:
    """앱 안 알림은 항상 켜져 있고, VAPID 개인키가 설정되면 웹 푸시 채널이 추가된다."""
    result: list = [InAppNotifier()]
    config = load_push_config()
    if config is not None:
        sender = PyWebPushSender(config.private_key, config.subject)
        result.append(WebPushNotifier(DjangoPushSubscriptionRepository(), sender))
    return result


def register() -> None:
    """프로세스당 한 번만 도메인 이벤트를 구독한다."""
    global _registered
    if _registered:
        return
    handlers = NotificationHandlers(NotificationService(channels()), DjangoUserDirectory())
    register_handlers(event_bus, handlers)
    _registered = True
