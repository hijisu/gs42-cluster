from rest_framework import serializers

from accounts.domain.role import Role


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    intra_id = serializers.CharField()
    name = serializers.CharField()
    image_url = serializers.URLField(allow_blank=True)
    role = serializers.CharField()
    slack_id = serializers.CharField(allow_null=True)


class MockLoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[r.value for r in Role])
