from django.conf import settings
from django.db import models


class PushSubscriptionRow(models.Model):
    """브라우저 푸시 구독. 한 사용자가 여러 기기를 가질 수 있다."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    endpoint = models.TextField()
    # endpoint 는 길 수 있어 해시로 유일성을 보장한다(sha256 hex).
    endpoint_hash = models.CharField(max_length=64, unique=True)
    p256dh = models.CharField(max_length=512)
    auth = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "notifications"
        db_table = "notifications_pushsubscription"
        indexes = [models.Index(fields=["user"])]
