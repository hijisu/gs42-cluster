from django.utils import timezone

from notifications.application.usecases import (
    ListNotificationsUseCase,
    MarkAllReadUseCase,
    MarkReadUseCase,
)
from notifications.infrastructure.repositories import DjangoNotificationRepository


def list_notifications() -> ListNotificationsUseCase:
    return ListNotificationsUseCase(DjangoNotificationRepository())


def mark_read() -> MarkReadUseCase:
    return MarkReadUseCase(DjangoNotificationRepository(), timezone.now)


def mark_all_read() -> MarkAllReadUseCase:
    return MarkAllReadUseCase(DjangoNotificationRepository(), timezone.now)
