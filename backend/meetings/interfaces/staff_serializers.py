from rest_framework import serializers

from meetings.application.ports import StaffMeetingTypeView, StaffMeetingView
from meetings.domain.meeting import MeetingStatus
from meetings.interfaces.serializers import meeting_payload


class AssignSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()


class ConfirmSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=128)
    staff_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    note = serializers.CharField(allow_blank=True, max_length=2000, default="")


class ProposeSerializer(serializers.Serializer):
    proposed_at = serializers.DateTimeField()
    note = serializers.CharField(allow_blank=True, max_length=2000, default="")


class StatusQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s.value for s in MeetingStatus], required=False)


class DateRangeSerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()

    def validate(self, attrs):
        if attrs["to_date"] < attrs["from_date"]:
            raise serializers.ValidationError("to는 from 이후여야 합니다")
        if (attrs["to_date"] - attrs["from_date"]).days > 31:
            raise serializers.ValidationError("조회 범위는 최대 31일입니다")
        return attrs


class AvailabilityPutSerializer(DateRangeSerializer):
    slots = serializers.ListField(child=serializers.DateTimeField(), max_length=2000)


class DefaultStaffItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    default_staff_id = serializers.IntegerField(allow_null=True)


def staff_meeting_payload(v: StaffMeetingView) -> dict:
    return {
        **meeting_payload(v.meeting),
        "student": {"id": v.student.id, "intra_id": v.student.intra_id, "name": v.student.name},
        "staff_note": v.staff_note,
        "created_at": v.created_at,
    }


def staff_type_payload(t: StaffMeetingTypeView) -> dict:
    return {
        "id": t.id,
        "code": t.code,
        "name": t.name,
        "default_staff": (
            {"id": t.default_staff_id, "name": t.default_staff_name} if t.default_staff_id else None
        ),
    }
