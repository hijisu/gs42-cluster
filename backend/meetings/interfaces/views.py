from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from meetings.application.usecases import RequestMeetingCommand
from meetings.domain.errors import MeetingTypeNotFound
from meetings.interfaces import deps
from meetings.interfaces.serializers import (
    RequestMeetingSerializer,
    SlotsQuerySerializer,
    meeting_payload,
    type_payload,
)


@api_view(["GET"])
def meeting_types(request):
    return Response([type_payload(t) for t in deps.meeting_types().list_all()])


def _type_param(request) -> dict:
    raw = request.query_params.get("type_id")
    return {} if raw is None else {"type_id": raw}


@api_view(["GET"])
def slots(request):
    query = SlotsQuerySerializer(
        data={
            "from_date": request.query_params.get("from"),
            "to_date": request.query_params.get("to"),
            **_type_param(request),
        }
    )
    query.is_valid(raise_exception=True)
    staff_id = None
    if "type_id" in query.validated_data:
        meeting_type = deps.meeting_types().get(query.validated_data["type_id"])
        if meeting_type is None:
            raise MeetingTypeNotFound("존재하지 않는 면담 유형입니다")
        staff_id = meeting_type.default_staff_id
    tz = timezone.get_current_timezone()
    start = datetime.combine(query.validated_data["from_date"], time.min, tzinfo=tz)
    end = datetime.combine(query.validated_data["to_date"], time.min, tzinfo=tz) + timedelta(days=1)
    result = deps.get_slots().execute(start, end - timedelta(microseconds=1), staff_id=staff_id)
    return Response(
        [
            {
                "start_at": s.start_at,
                "state": s.state,
                "available": s.available,
                "remaining": s.remaining,
            }
            for s in result
        ]
    )


@api_view(["POST"])
def create_meeting(request):
    body = RequestMeetingSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        view = deps.request_meeting().execute(
            RequestMeetingCommand(student_id=request.user.pk, **body.validated_data)
        )
    return Response(meeting_payload(view), status=status.HTTP_201_CREATED)


@api_view(["GET"])
def my_meetings(request):
    views = deps.list_my_meetings().execute(request.user.pk)
    return Response([meeting_payload(v) for v in views])


@api_view(["POST"])
def cancel(request, meeting_id: int):
    with transaction.atomic():
        view = deps.cancel_meeting().execute(meeting_id, request.user.pk)
    return Response(meeting_payload(view))


@api_view(["POST"])
def accept_proposal(request, meeting_id: int):
    with transaction.atomic():
        view = deps.accept_meeting_proposal().execute(meeting_id, request.user.pk)
    return Response(meeting_payload(view))
