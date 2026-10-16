from django.contrib.auth import get_user_model
from django.db import transaction

from notifications.domain.notification import Notification, NotificationType
from notifications.infrastructure.models import NotificationRow


def _to_domain(row: NotificationRow) -> Notification:
    return Notification(
        id=row.pk,
        user_id=row.user_id,
        type=NotificationType(row.type),
        title=row.title,
        body=row.body,
        link=row.link,
        data=row.data,
        created_at=row.created_at,
        read_at=row.read_at,
    )


class DjangoNotificationRepository:
    def add(self, notification: Notification) -> Notification:
        row = NotificationRow.objects.create(
            user_id=notification.user_id,
            type=notification.type.value,
            title=notification.title,
            body=notification.body,
            link=notification.link,
            data=notification.data,
        )
        notification.id, notification.created_at = row.pk, row.created_at
        return notification

    def get(self, notification_id: int) -> Notification | None:
        row = NotificationRow.objects.filter(pk=notification_id).first()
        return _to_domain(row) if row else None

    def save(self, notification: Notification) -> None:
        NotificationRow.objects.filter(pk=notification.id).update(read_at=notification.read_at)

    def list_for_user(self, user_id: int, unread_only: bool, limit: int) -> list[Notification]:
        qs = NotificationRow.objects.filter(user_id=user_id)
        if unread_only:
            qs = qs.filter(read_at__isnull=True)
        return [_to_domain(r) for r in qs.order_by("-created_at", "-id")[:limit]]

    def unread_count(self, user_id: int) -> int:
        return NotificationRow.objects.filter(user_id=user_id, read_at__isnull=True).count()

    def mark_all_read(self, user_id: int, now) -> int:
        return NotificationRow.objects.filter(user_id=user_id, read_at__isnull=True).update(
            read_at=now
        )


class InAppNotifier:
    """앱 안 알림 채널: DB에 저장한다. 항상 켜져 있는 기본 채널."""

    name = "in_app"

    def __init__(self, repo: DjangoNotificationRepository | None = None) -> None:
        self._repo = repo or DjangoNotificationRepository()

    def send(self, notification: Notification) -> None:
        # savepoint: 저장 실패가 바깥 요청의 트랜잭션을 망가뜨리지 않게 한다.
        with transaction.atomic():
            self._repo.add(notification)


class DjangoUserDirectory:
    def ids_by_intra_ids(self, intra_ids: list[str]) -> dict[str, int]:
        wanted = {i.lower() for i in intra_ids}
        users = get_user_model().objects.all().values_list("intra_id", "pk")
        return {intra.lower(): pk for intra, pk in users if intra.lower() in wanted}
