from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from notifications.application.push import SubscribePushUseCase, UnsubscribePushUseCase
from notifications.infrastructure.push import DjangoPushSubscriptionRepository
from notifications.interfaces.push_config import load_push_config
from notifications.interfaces.push_serializers import SubscribeSerializer, UnsubscribeSerializer


def _not_configured() -> Response:
    return Response(
        {"code": "push_not_configured", "detail": "웹 푸시가 설정되지 않았습니다"},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@api_view(["GET"])
def public_key(request):
    config = load_push_config()
    if config is None:
        return _not_configured()
    return Response({"public_key": config.public_key})


@api_view(["POST", "DELETE"])
def subscriptions(request):
    if request.method == "DELETE":
        body = UnsubscribeSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        UnsubscribePushUseCase(DjangoPushSubscriptionRepository()).execute(
            request.user.pk, body.validated_data["endpoint"]
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    if load_push_config() is None:
        return _not_configured()
    body = SubscribeSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    keys = body.validated_data["keys"]
    subscription = SubscribePushUseCase(DjangoPushSubscriptionRepository()).execute(
        request.user.pk, body.validated_data["endpoint"], keys["p256dh"], keys["auth"]
    )
    return Response({"id": subscription.id}, status=status.HTTP_201_CREATED)
