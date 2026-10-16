from rest_framework import serializers

from rooms.application.ports import StaffReservationView
from rooms.domain.reservation import ReservationStatus
from rooms.domain.room import RoomStatus
from rooms.interfaces.serializers import reservation_payload


class StaffListQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    status = serializers.ChoiceField(choices=[s.value for s in ReservationStatus], required=False)


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)


class ReassignSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()


class StaffBookingSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    purpose = serializers.CharField(max_length=100)
    headcount = serializers.IntegerField(min_value=1, max_value=100)
    note = serializers.CharField(allow_blank=True, max_length=2000, default="")
    user_id = serializers.IntegerField(required=False, allow_null=True, default=None)


class RulesSerializer(serializers.Serializer):
    open_hour = serializers.IntegerField(min_value=0, max_value=24)
    close_hour = serializers.IntegerField(min_value=0, max_value=24)
    usage_rules = serializers.ListField(
        child=serializers.CharField(max_length=300, allow_blank=True), max_length=30
    )


class RoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64)
    code = serializers.SlugField(max_length=32, required=False, allow_null=True, default=None)
    capacity_note = serializers.CharField(allow_blank=True, max_length=64, default="")
    equipment = serializers.CharField(allow_blank=True, max_length=128, default="")


class RoomPatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=False)
    capacity_note = serializers.CharField(allow_blank=True, max_length=64, required=False)
    equipment = serializers.CharField(allow_blank=True, max_length=128, required=False)
    status = serializers.ChoiceField(choices=[s.value for s in RoomStatus], required=False)


def staff_reservation_payload(v: StaffReservationView) -> dict:
    return {
        **reservation_payload(v.view),
        "user": {"id": v.user.id, "intra_id": v.user.intra_id, "name": v.user.name},
        "created_by_staff": v.created_by_staff,
        "conflict_ids": v.conflict_ids,
    }
