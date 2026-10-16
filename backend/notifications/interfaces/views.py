from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from notifications.interfaces import deps
from notifications.interfaces.serializers import ListQuerySerializer, notification_payload


@api_view(["GET"])
def list_notifications(request):
    query = ListQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    result = deps.list_notifications().execute(
        request.user.pk, query.validated_data["unread"], query.validated_data["limit"]
    )
    return Response(
        {
            "unread_count": result.unread_count,
            "items": [notification_payload(n) for n in result.items],
        }
    )


@api_view(["POST"])
def read(request, notification_id: int):
    with transaction.atomic():
        notification = deps.mark_read().execute(notification_id, request.user.pk)
    return Response(notification_payload(notification))


@api_view(["POST"])
def read_all(request):
    with transaction.atomic():
        updated = deps.mark_all_read().execute(request.user.pk)
    return Response({"updated": updated})
