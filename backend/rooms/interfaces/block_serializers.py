from rest_framework import serializers

from rooms.application.block_usecases import BlockResult
from rooms.domain.block import Repeat
from rooms.domain.reservation import RoomReservation


class BlockWriteSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    reason = serializers.CharField(max_length=200)
    repeat = serializers.ChoiceField(choices=[r.value for r in Repeat], default=Repeat.NONE.value)
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6), max_length=7, default=list
    )
    until = serializers.DateField(required=False, allow_null=True, default=None)
    check_only = serializers.BooleanField(default=False)


class BlockPatchSerializer(BlockWriteSerializer):
    room_id = serializers.IntegerField(required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)
    reason = serializers.CharField(max_length=200, required=False)
    repeat = serializers.ChoiceField(choices=[r.value for r in Repeat], required=False)
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6), max_length=7, required=False
    )
    until = serializers.DateField(required=False, allow_null=True)


class OccurrencePatchSerializer(serializers.Serializer):
    room_id = serializers.IntegerField(required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)
    reason = serializers.CharField(max_length=200, required=False)
    check_only = serializers.BooleanField(default=False)


class BlockQuerySerializer(serializers.Serializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    room_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if attrs["to_date"] < attrs["from_date"]:
            raise serializers.ValidationError("to는 from 이후여야 합니다")
        if (attrs["to_date"] - attrs["from_date"]).days > 366:
            raise serializers.ValidationError("조회 범위는 최대 366일입니다")
        return attrs


def _reservation_ref(r: RoomReservation) -> dict:
    return {
        "id": r.id,
        "room_id": r.room_id,
        "start_at": r.time_range.start,
        "end_at": r.time_range.end,
        "status": r.status.value,
        "purpose": r.purpose,
    }


def block_payload(block, occurrences) -> dict:
    return {
        "id": block.id,
        "room_id": block.room_id,
        "start_at": block.time_range.start,
        "end_at": block.time_range.end,
        "reason": block.reason,
        "repeat": block.repeat.value,
        "weekdays": sorted(block.weekdays),
        "until": block.until,
        "occurrences": [
            {"date": o.day, "start_at": o.time_range.start, "end_at": o.time_range.end}
            for o in occurrences
        ],
    }


def block_result_payload(result: BlockResult, saved: bool = True) -> dict:
    return {
        "block": block_payload(result.block, result.occurrences),
        "saved": saved,
        "conflicting_reservations": [_reservation_ref(r) for r in result.conflicting],
    }
