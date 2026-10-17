import hashlib
import json

from pywebpush import WebPushException, webpush

from notifications.application.push import SubscriptionGone
from notifications.domain.push import PushSubscription
from notifications.infrastructure.push_models import PushSubscriptionRow


def endpoint_hash(endpoint: str) -> str:
    return hashlib.sha256(endpoint.encode()).hexdigest()


def _to_domain(row: PushSubscriptionRow) -> PushSubscription:
    return PushSubscription(
        id=row.pk,
        user_id=row.user_id,
        endpoint=row.endpoint,
        p256dh=row.p256dh,
        auth=row.auth,
        created_at=row.created_at,
    )


class DjangoPushSubscriptionRepository:
    def upsert(self, subscription: PushSubscription) -> PushSubscription:
        row, _ = PushSubscriptionRow.objects.update_or_create(
            endpoint_hash=endpoint_hash(subscription.endpoint),
            defaults={
                "user_id": subscription.user_id,  # 같은 브라우저를 다른 계정이 쓰면 소유권을 옮긴다
                "endpoint": subscription.endpoint,
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        )
        return _to_domain(row)

    def list_for_user(self, user_id: int) -> list[PushSubscription]:
        return [
            _to_domain(r)
            for r in PushSubscriptionRow.objects.filter(user_id=user_id).order_by("id")
        ]

    def delete(self, user_id: int, endpoint: str) -> bool:
        deleted, _ = PushSubscriptionRow.objects.filter(
            user_id=user_id, endpoint_hash=endpoint_hash(endpoint)
        ).delete()
        return deleted > 0

    def delete_endpoint(self, endpoint: str) -> None:
        PushSubscriptionRow.objects.filter(endpoint_hash=endpoint_hash(endpoint)).delete()


GONE_STATUSES = {404, 410}


class PyWebPushSender:
    """pywebpush 로 payload 를 암호화(aes128gcm)하고 VAPID 서명을 붙여 푸시 서비스로 보낸다."""

    def __init__(
        self, private_key: str, subject: str, timeout: float = 10.0, ttl: int = 3600
    ) -> None:
        self._private_key = private_key
        self._subject = subject
        self._timeout = timeout
        self._ttl = ttl

    def send(self, subscription: PushSubscription, payload: dict) -> None:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=self._private_key,
                vapid_claims={"sub": self._subject},
                timeout=self._timeout,
                ttl=self._ttl,
            )
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in GONE_STATUSES:
                raise SubscriptionGone() from exc
            raise
