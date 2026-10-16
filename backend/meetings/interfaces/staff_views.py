"""운영팀 전용 면담 API. 모든 뷰에 IsStaff를 적용한다."""

from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response

from accounts.interfaces.decorators import staff_api
from meetings.application.staff_usecases import ConfirmCommand, ProposeCommand
from meetings.interfaces import deps
from meetings.interfaces.staff_serializers import (
    AssignSerializer,
    AvailabilityPutSerializer,
    ConfirmSerializer,
    DateRangeSerializer,
    DefaultStaffItemSerializer,
    ProposeSerializer,
    StatusQuerySerializer,
    staff_meeting_payload,
    staff_type_payload,
)


def _range(start_date, end_date):
    tz = timezone.get_current_timezone()
    start = datetime.combine(start_date, time.min, tzinfo=tz)
    end = (
        datetime.combine(end_date, time.min, tzinfo=tz)
        + timedelta(days=1)
        - timedelta(microseconds=1)
    )
    return start, end


@staff_api(["GET"])
def list_meetings(request):
    query = StatusQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    views = deps.list_staff_meetings().execute(query.validated_data.get("status"))
    return Response([staff_meeting_payload(v) for v in views])


@staff_api(["PATCH"])
def assign(request, meeting_id: int):
    body = AssignSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.assign_meeting().execute(meeting_id, body.validated_data["staff_id"])
    return Response(staff_meeting_payload(view))


@staff_api(["POST"])
def confirm(request, meeting_id: int):
    body = ConfirmSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.confirm_meeting().execute(
            ConfirmCommand(
                meeting_id=meeting_id,
                acting_staff_id=request.user.pk,
                location=body.validated_data["location"],
                staff_id=body.validated_data["staff_id"],
                note=body.validated_data["note"],
            )
        )
    return Response(staff_meeting_payload(view))


@staff_api(["POST"])
def propose(request, meeting_id: int):
    body = ProposeSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.propose_meeting().execute(
            ProposeCommand(
                meeting_id=meeting_id,
                acting_staff_id=request.user.pk,
                proposed_at=body.validated_data["proposed_at"],
                note=body.validated_data["note"],
            )
        )
    return Response(staff_meeting_payload(view))


@staff_api(["GET", "PUT"])
def availability(request):
    if request.method == "GET":
        query = DateRangeSerializer(
            data={
                "from_date": request.query_params.get("from"),
                "to_date": request.query_params.get("to"),
            }
        )
        query.is_valid(raise_exception=True)
        start, end = _range(query.validated_data["from_date"], query.validated_data["to_date"])
        slots = deps.get_availability().execute(request.user.pk, start, end)
    else:
        body = AvailabilityPutSerializer(
            data={
                "from_date": request.data.get("from"),
                "to_date": request.data.get("to"),
                "slots": request.data.get("slots"),
            }
        )
        body.is_valid(raise_exception=True)
        start, end = _range(body.validated_data["from_date"], body.validated_data["to_date"])
        with transaction.atomic():
            slots = deps.set_availability().execute(
                request.user.pk, start, end, body.validated_data["slots"]
            )
    return Response({"slots": slots})


@staff_api(["GET", "PUT"])
def meeting_types(request):
    if request.method == "PUT":
        body = DefaultStaffItemSerializer(data=request.data, many=True)
        body.is_valid(raise_exception=True)
        assignments = {item["id"]: item["default_staff_id"] for item in body.validated_data}
        with transaction.atomic():
            views = deps.set_default_staff().execute(assignments)
    else:
        views = deps.staff_meeting_types().execute()
    return Response([staff_type_payload(t) for t in views])
