from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from accounts.domain.role import Role
from meetings.application.ports import (
    MeetingTypeInfo,
    MeetingView,
    StaffMeetingTypeView,
    StaffMeetingView,
    StudentInfo,
)
from meetings.domain.errors import MeetingNotFound, SlotUnavailable
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
        try:
            with transaction.atomic():  # savepoint: 제약 위반 후에도 바깥 트랜잭션 유지
                MeetingRequestRow.objects.filter(pk=meeting.id).update(**_fields(meeting))
        except IntegrityError as exc:
            raise SlotUnavailable("같은 담당자의 같은 시간에 이미 확정된 면담이 있습니다") from exc

    def has_confirmed(self, staff_id: int, at: datetime, exclude_id: int | None) -> bool:
        qs = MeetingRequestRow.objects.filter(
            status=MeetingStatus.CONFIRMED.value, staff_id=staff_id, slot_at=at
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    def staff_has_confirmed_between(
        self, staff_id: int, start: datetime, end: datetime
    ) -> list[datetime]:
        return list(
            MeetingRequestRow.objects.filter(
                status=MeetingStatus.CONFIRMED.value,
                staff_id=staff_id,
                slot_at__gte=start,
                slot_at__lte=end,
            ).values_list("slot_at", flat=True)
        )

    def confirmed_between(
        self, start: datetime, end: datetime
    ) -> list[tuple[int | None, datetime]]:
        rows = MeetingRequestRow.objects.filter(
            status=MeetingStatus.CONFIRMED.value, slot_at__gte=start, slot_at__lte=end
        ).values_list("staff_id", "slot_at")
        return list(rows)


class DjangoAvailabilityRepository:
    def for_staff_between(self, staff_id: int, start: datetime, end: datetime) -> list[datetime]:
        rows = AvailabilitySlot.objects.filter(
            staff_id=staff_id, start_at__gte=start, start_at__lte=end
        ).order_by("start_at")
        return list(rows.values_list("start_at", flat=True))

    @transaction.atomic
    def replace_for_staff(
        self, staff_id: int, start: datetime, end: datetime, slots: list[datetime]
    ) -> None:
        AvailabilitySlot.objects.filter(
            staff_id=staff_id, start_at__gte=start, start_at__lte=end
        ).exclude(start_at__in=slots).delete()
        existing = set(
            AvailabilitySlot.objects.filter(staff_id=staff_id, start_at__in=slots).values_list(
                "start_at", flat=True
            )
        )
        AvailabilitySlot.objects.bulk_create(
            [AvailabilitySlot(staff_id=staff_id, start_at=t) for t in slots if t not in existing]
        )

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

    def set_default_staff(self, type_id: int, staff_id: int | None) -> None:
        MeetingType.objects.filter(pk=type_id).update(default_staff_id=staff_id)


class DjangoStaffDirectory:
    def is_staff(self, user_id: int) -> bool:
        return (
            get_user_model()
            .objects.filter(pk=user_id, role=Role.STAFF.value, is_active=True)
            .exists()
        )


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


class DjangoStaffMeetingReadModel:
    def _qs(self):
        return MeetingRequestRow.objects.select_related("type", "staff", "student")

    @staticmethod
    def _staff_view(row: MeetingRequestRow) -> StaffMeetingView:
        return StaffMeetingView(
            meeting=_view(row),
            student=StudentInfo(
                id=row.student_id, intra_id=row.student.intra_id, name=row.student.name
            ),
            staff_note=row.staff_note,
            created_at=row.created_at,
        )

    def get(self, meeting_id: int) -> StaffMeetingView:
        row = self._qs().filter(pk=meeting_id).first()
        if row is None:
            raise MeetingNotFound("면담을 찾을 수 없습니다")
        return self._staff_view(row)

    def list_meetings(self, status: str | None) -> list[StaffMeetingView]:
        qs = self._qs().order_by("slot_at", "id")
        if status:
            qs = qs.filter(status=status)
        return [self._staff_view(r) for r in qs]

    def list_types(self) -> list[StaffMeetingTypeView]:
        return [
            StaffMeetingTypeView(
                id=t.pk,
                code=t.code,
                name=t.name,
                default_staff_id=t.default_staff_id,
                default_staff_name=t.default_staff.name if t.default_staff else None,
            )
            for t in MeetingType.objects.select_related("default_staff")
        ]
