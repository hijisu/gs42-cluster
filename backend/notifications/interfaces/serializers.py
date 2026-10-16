from rest_framework import serializers

from notifications.domain.notification import Notification


class ListQuerySerializer(serializers.Serializer):
    unread = serializers.BooleanField(required=False, default=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=50)


def notification_payload(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type.value,
        "title": n.title,
        "body": n.body,
        "link": n.link,
        "data": n.data,
        "read": n.is_read,
        "read_at": n.read_at,
        "created_at": n.created_at,
    }
