from django.conf import settings
from django.db import models

from notifications.domain.notification import NotificationType


class NotificationRow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    type = models.CharField(max_length=32, choices=[(t.value, t.name) for t in NotificationType])
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=200, blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "notifications"
        db_table = "notifications_notification"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "read_at"]),
        ]
