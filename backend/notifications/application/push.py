"""웹 푸시 채널: 구독 관리와 알림 전송."""

import logging
from typing import Protocol

from notifications.domain.notification import Notification
from notifications.domain.push import PushSubscription

logger = logging.getLogger(__name__)


class SubscriptionGone(Exception):
    """푸시 서비스가 구독이 만료/해지되었다고 알림(404/410). 구독을 지워야 한다."""


class PushSender(Protocol):
    def send(self, subscription: PushSubscription, payload: dict) -> None:
        """암호화·VAPID 서명 후 전송한다. 만료면 SubscriptionGone, 그 외 실패는 예외."""
        ...


class PushSubscriptionRepository(Protocol):
    def upsert(self, subscription: PushSubscription) -> PushSubscription:
        """endpoint 기준으로 저장한다. 다른 사용자의 구독이면 현재 사용자로 소유권을 옮긴다."""
        ...

    def list_for_user(self, user_id: int) -> list[PushSubscription]: ...

    def delete(self, user_id: int, endpoint: str) -> bool: ...

    def delete_endpoint(self, endpoint: str) -> None: ...


class SubscribePushUseCase:
    def __init__(self, repo: PushSubscriptionRepository) -> None:
        self._repo = repo

    def execute(self, user_id: int, endpoint: str, p256dh: str, auth: str) -> PushSubscription:
        return self._repo.upsert(PushSubscription.create(user_id, endpoint, p256dh, auth))


class UnsubscribePushUseCase:
    def __init__(self, repo: PushSubscriptionRepository) -> None:
        self._repo = repo

    def execute(self, user_id: int, endpoint: str) -> None:
        """멱등: 없는 구독을 지워도 성공으로 본다. 남의 구독은 지우지 못한다."""
        self._repo.delete(user_id, endpoint)


def push_payload(notification: Notification) -> dict:
    """서비스워커(frontend/src/sw.ts)가 읽는 형식: {title, body, link} + 종류 코드."""
    return {
        "title": notification.title,
        "body": notification.body,
        "link": notification.link,
        "type": notification.type.value,
    }


class WebPushNotifier:
    """Notifier 채널. 구독이 없으면 건너뛰고(앱 안 알림만), 구독별 실패는 서로 격리한다."""

    name = "web_push"

    def __init__(self, repo: PushSubscriptionRepository, sender: PushSender) -> None:
        self._repo = repo
        self._sender = sender

    def send(self, notification: Notification) -> None:
        subscriptions = self._repo.list_for_user(notification.user_id)
        if not subscriptions:
            return
        payload = push_payload(notification)
        for subscription in subscriptions:
            try:
                self._sender.send(subscription, payload)
            except SubscriptionGone:
                self._repo.delete_endpoint(subscription.endpoint)
                logger.info("만료된 푸시 구독 삭제: user=%s", subscription.user_id)
            except Exception:
                logger.exception(
                    "웹 푸시 전송 실패: user=%s sub=%s", subscription.user_id, subscription.id
                )
