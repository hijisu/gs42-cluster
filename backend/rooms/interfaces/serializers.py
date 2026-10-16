from rest_framework import serializers

from rooms.application.ports import ReservationView, RoomInfo
from rooms.application.usecases import RoomAvailability
from rooms.domain.rules import RoomRules


class ReservationRequestSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    purpose = serializers.CharField(max_length=100)
    headcount = serializers.IntegerField(min_value=1, max_value=100)
    note = serializers.CharField(allow_blank=True, max_length=2000, default="")


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()


def room_payload(r: RoomInfo) -> dict:
    return {
        "id": r.id,
        "code": r.code,
        "name": r.name,
        "capacity_note": r.capacity_note,
        "equipment": r.equipment,
        "status": r.status,
    }


def reservation_payload(v: ReservationView) -> dict:
    return {
        "id": v.id,
        "room": room_payload(v.room),
        "requested_room": room_payload(v.requested_room),
        "start_at": v.start_at,
        "end_at": v.end_at,
        "purpose": v.purpose,
        "headcount": v.headcount,
        "note": v.note,
        "status": v.status,
        "reject_reason": v.reject_reason,
        "conflict": v.conflict,
    }


def rules_payload(rules: RoomRules) -> dict:
    return {
        "open_hour": rules.open_hour,
        "close_hour": rules.close_hour,
        "step_minutes": rules.step_minutes,
        "usage_rules": list(rules.usage_rules),
    }


def availability_payload(day, items: list[RoomAvailability]) -> dict:
    return {
        "date": day.isoformat(),
        "rooms": [
            {
                "room": room_payload(item.room),
                "hours": [{"hour": h, "state": s} for h, s in item.hours],
                "reservations": [
                    {
                        "id": b.reservation_id,
                        "start_at": b.start_at,
                        "end_at": b.end_at,
                        "status": b.status,
                        "purpose": b.purpose,
                        "headcount": b.headcount,
                        "mine": b.mine,
                    }
                    for b in item.blocks
                ],
            }
            for item in items
        ],
    }
