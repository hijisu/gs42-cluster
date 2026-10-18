from rest_framework import serializers

from meetings.application.ports import MeetingTypeInfo, MeetingView


class RequestMeetingSerializer(serializers.Serializer):
    type_id = serializers.IntegerField()
    slot_at = serializers.DateTimeField()
    content = serializers.CharField(allow_blank=True, max_length=2000, default="")
    notify_slack = serializers.BooleanField(default=False)


class SlotsQuerySerializer(serializers.Serializer):
    # from은 파이썬 예약어라 필드명은 from_date, 쿼리 이름은 source로 맞춘다.
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    # 선택한 면담 유형. 있으면 그 유형 기본 담당자의 가능 시간만 보여준다.
    type_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if attrs["to_date"] < attrs["from_date"]:
            raise serializers.ValidationError("to는 from 이후여야 합니다")
        if (attrs["to_date"] - attrs["from_date"]).days > 31:
            raise serializers.ValidationError("조회 범위는 최대 31일입니다")
        return attrs


def type_payload(t: MeetingTypeInfo) -> dict:
    return {"id": t.id, "code": t.code, "name": t.name}


def meeting_payload(v: MeetingView) -> dict:
    return {
        "id": v.id,
        "type": type_payload(v.type),
        "slot_at": v.slot_at,
        "content": v.content,
        "notify_slack": v.notify_slack,
        "status": v.status,
        "staff": {"id": v.staff_id, "name": v.staff_name} if v.staff_id else None,
        "location": v.location,
        "proposed_at": v.proposed_at,
    }
