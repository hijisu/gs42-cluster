from datetime import datetime

from meetings.application.ports import MeetingTypeInfo, MeetingView
from meetings.domain.errors import MeetingNotFound
from meetings.domain.meeting import MeetingRequest, MeetingStatus
from meetings.infrastructure.models import AvailabilitySlot, MeetingRequestRow, MeetingType


def _to_domain(row: MeetingRequestRow) -> MeetingRequest:
    return MeetingRequest(
        id=row.pk,
        student_id=row.student_id,
        type_id=row.type_id,
        slot_at=row.slot_at,
        content=row.content,
        notify_slack=row.notify_slack,
        staff_id=row.staff_id,
        status=MeetingStatus(row.status),
        location=row.location,
        proposed_at=row.proposed_at,
        staff_note=row.staff_note,
    )


def _fields(meeting: MeetingRequest) -> dict:
    return {
        "student_id": meeting.student_id,
        "type_id": meeting.type_id,
        "slot_at": meeting.slot_at,
        "content": meeting.content,
        "notify_slack": meeting.notify_slack,
        "staff_id": meeting.staff_id,
        "status": meeting.status.value,
        "location": meeting.location,
        "proposed_at": meeting.proposed_at,
        "staff_note": meeting.staff_note,
    }


class DjangoMeetingRepository:
    def add(self, meeting: MeetingRequest) -> MeetingRequest:
        row = MeetingRequestRow.objects.create(**_fields(meeting))
        meeting.id = row.pk
        return meeting

    def get(self, meeting_id: int) -> MeetingRequest | None:
        row = MeetingRequestRow.objects.filter(pk=meeting_id).first()
        return _to_domain(row) if row else None

    def save(self, meeting: MeetingRequest) -> None:
        MeetingRequestRow.objects.filter(pk=meeting.id).update(**_fields(meeting))

    def confirmed_between(
        self, start: datetime, end: datetime
    ) -> list[tuple[int | None, datetime]]:
        rows = MeetingRequestRow.objects.filter(
            status=MeetingStatus.CONFIRMED.value, slot_at__gte=start, slot_at__lte=end
        ).values_list("staff_id", "slot_at")
        return list(rows)


class DjangoAvailabilityRepository:
    def offered_between(self, start: datetime, end: datetime) -> list[tuple[int, datetime]]:
        rows = AvailabilitySlot.objects.filter(start_at__gte=start, start_at__lte=end)
        return list(rows.values_list("staff_id", "start_at"))


def _type_info(row: MeetingType) -> MeetingTypeInfo:
    return MeetingTypeInfo(
        id=row.pk, code=row.code, name=row.name, default_staff_id=row.default_staff_id
    )


class DjangoMeetingTypeRepository:
    def list_all(self) -> list[MeetingTypeInfo]:
        return [_type_info(r) for r in MeetingType.objects.all()]

    def get(self, type_id: int) -> MeetingTypeInfo | None:
        row = MeetingType.objects.filter(pk=type_id).first()
        return _type_info(row) if row else None


def _view(row: MeetingRequestRow) -> MeetingView:
    return MeetingView(
        id=row.pk,
        type=_type_info(row.type),
        slot_at=row.slot_at,
        content=row.content,
        notify_slack=row.notify_slack,
        status=row.status,
        staff_id=row.staff_id,
        staff_name=row.staff.name if row.staff else None,
        location=row.location,
        proposed_at=row.proposed_at,
    )


class DjangoMeetingReadModel:
    def _qs(self):
        return MeetingRequestRow.objects.select_related("type", "staff")

    def get_view(self, meeting_id: int) -> MeetingView:
        row = self._qs().filter(pk=meeting_id).first()
        if row is None:
            raise MeetingNotFound("면담을 찾을 수 없습니다")
        return _view(row)

    def list_for_student(self, student_id: int) -> list[MeetingView]:
        rows = self._qs().filter(student_id=student_id).order_by("-slot_at", "-id")
        return [_view(r) for r in rows]
