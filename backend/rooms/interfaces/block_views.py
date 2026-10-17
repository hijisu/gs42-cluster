"""운영팀 전용 예약 차단 기간 API. 모든 뷰에 IsStaff를 적용한다."""

from datetime import date, datetime, time, timedelta

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from accounts.interfaces.decorators import staff_api
from rooms.application.block_usecases import BlockCommand
from rooms.domain.rules import KST
from rooms.interfaces import staff_deps as deps
from rooms.interfaces.block_serializers import (
    BlockPatchSerializer,
    BlockQuerySerializer,
    BlockWriteSerializer,
    OccurrencePatchSerializer,
    block_payload,
    block_result_payload,
)


def _parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        from rooms.domain.errors import InvalidBlock

        raise InvalidBlock("날짜 형식은 YYYY-MM-DD 입니다") from None


@staff_api(["GET", "POST"])
def blocks(request):
    if request.method == "GET":
        raw = {
            "from_date": request.query_params.get("from"),
            "to_date": request.query_params.get("to"),
            "room_id": request.query_params.get("room_id"),
        }
        query = BlockQuerySerializer(data={k: v for k, v in raw.items() if v is not None})
        query.is_valid(raise_exception=True)
        data = query.validated_data
        start = datetime.combine(data["from_date"], time.min, tzinfo=KST)
        end = datetime.combine(data["to_date"], time.min, tzinfo=KST) + timedelta(days=1)
        found = deps.list_blocks().execute(start, end, data.get("room_id"))
        return Response([block_payload(b, occ) for b, occ in found])
    body = BlockWriteSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    data = dict(body.validated_data)
    dry_run = data.pop("check_only")
    cmd = BlockCommand(
        room_id=data["room_id"],
        start_at=data["start_at"],
        end_at=data["end_at"],
        reason=data["reason"],
        repeat=data["repeat"],
        weekdays=tuple(data["weekdays"]),
        until=data["until"],
    )
    with transaction.atomic():
        result = deps.create_block().execute(cmd, request.user.pk, dry_run=dry_run)
    return Response(
        block_result_payload(result, saved=not dry_run),
        status=status.HTTP_200_OK if dry_run else status.HTTP_201_CREATED,
    )


@staff_api(["PATCH", "DELETE"])
def block_detail(request, block_id: int):
    if request.method == "DELETE":
        deps.delete_block().execute(block_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    body = BlockPatchSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    changes = dict(body.validated_data)
    dry_run = changes.pop("check_only", False)
    with transaction.atomic():
        result = deps.update_block().execute(block_id, changes, dry_run=dry_run)
    return Response(block_result_payload(result, saved=not dry_run))


@staff_api(["PATCH", "DELETE"])
def block_occurrence(request, block_id: int, day: str):
    when = _parse_day(day)
    if request.method == "DELETE":
        with transaction.atomic():
            deps.skip_occurrence().execute(block_id, when)
        return Response(status=status.HTTP_204_NO_CONTENT)
    body = OccurrencePatchSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    changes = dict(body.validated_data)
    dry_run = changes.pop("check_only", False)
    with transaction.atomic():
        result = deps.update_occurrence().execute(
            block_id, when, changes, request.user.pk, dry_run=dry_run
        )
    return Response(block_result_payload(result, saved=not dry_run))
