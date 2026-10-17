from rest_framework import serializers


class KeysSerializer(serializers.Serializer):
    p256dh = serializers.CharField(max_length=512)
    auth = serializers.CharField(max_length=512)


class SubscribeSerializer(serializers.Serializer):
    """브라우저의 PushSubscription.toJSON() 형식: {endpoint, expirationTime, keys}"""

    endpoint = serializers.CharField(max_length=2000)
    expirationTime = serializers.IntegerField(required=False, allow_null=True)  # noqa: N815
    keys = KeysSerializer()


class UnsubscribeSerializer(serializers.Serializer):
    endpoint = serializers.CharField(max_length=2000)
