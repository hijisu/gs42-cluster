"""교육운영팀용 유스케이스."""

from dataclasses import dataclass
from datetime import date, datetime

from common.domain.events import EventDispatcher
from meetings.application.ports import (
    AvailabilityRepository,
    MeetingRepository,
    MeetingTypeRepository,
    StaffDirectory,
    StaffMeetingReadModel,
    StaffMeetingTypeView,
    StaffMeetingView,
)
from meetings.application.usecases import Clock
from meetings.domain import availability_window
from meetings.domain.defaults import KST
from meetings.domain.errors import (
    InvalidSlot,
    MeetingNotFound,
    MeetingTypeNotFound,
    SlotHasMeeting,
    SlotUnavailable,
    StaffNotFound,
)
from meetings.domain.events import MeetingConfirmed, MeetingProposed
from meetings.domain.meeting import MeetingRequest
from meetings.domain.slots import is_aligned


def _load(meetings: MeetingRepository, meeting_id: int) -> MeetingRequest:
    meeting = meetings.get(meeting_id)
    if meeting is None:
        raise MeetingNotFound("면담을 찾을 수 없습니다")
    return meeting


def _require_staff(directory: StaffDirectory, staff_id: int) -> None:
    if not directory.is_staff(staff_id):
        raise StaffNotFound("운영팀 계정이 아닙니다")


class ListStaffMeetingsUseCase:
    def __init__(self, read_model: StaffMeetingReadModel) -> None:
        self._read = read_model

    def execute(self, status: str | None) -> list[StaffMeetingView]:
        return self._read.list_meetings(status)


class AssignMeetingUseCase:
    def __init__(
        self,
        meetings: MeetingRepository,
        directory: StaffDirectory,
        read_model: StaffMeetingReadModel,
    ) -> None:
        self._meetings = meetings
        self._directory = directory
        self._read = read_model

    def execute(self, meeting_id: int, staff_id: int) -> StaffMeetingView:
        _require_staff(self._directory, staff_id)
        meeting = _load(self._meetings, meeting_id)
        meeting.assign(staff_id)
        self._meetings.save(meeting)
        return self._read.get(meeting_id)


@dataclass(frozen=True)
class ConfirmCommand:
    meeting_id: int
    acting_staff_id: int
    location: str
    staff_id: int | None = None
    note: str = ""


class ConfirmMeetingUseCase:
    def __init__(
        self,
        meetings: MeetingRepository,
        directory: StaffDirectory,
        read_model: StaffMeetingReadModel,
        events: EventDispatcher,
    ) -> None:
        self._meetings = meetings
        self._directory = directory
        self._read = read_model
        self._events = events

    def execute(self, cmd: ConfirmCommand) -> StaffMeetingView:
        meeting = _load(self._meetings, cmd.meeting_id)
        staff_id = cmd.staff_id or meeting.staff_id or cmd.acting_staff_id
        _require_staff(self._directory, staff_id)
        meeting.confirm(staff_id=staff_id, location=cmd.location, note=cmd.note)
        # 같은 담당자·같은 시각의 확정이 이미 있으면 막는다(DB 부분 유니크 제약이 최종 방어선).
        if self._meetings.has_confirmed(staff_id, meeting.slot_at, exclude_id=meeting.id):
            raise SlotUnavailable("같은 담당자의 같은 시간에 이미 확정된 면담이 있습니다")
        self._meetings.save(meeting)
        self._events.publish(
            MeetingConfirmed(
                meeting_id=meeting.id,
                student_id=meeting.student_id,
                staff_id=staff_id,
                slot_at=meeting.slot_at,
                location=meeting.location,
            )
        )
        return self._read.get(meeting.id)


@dataclass(frozen=True)
class ProposeCommand:
    meeting_id: int
    acting_staff_id: int
    proposed_at: datetime
    note: str = ""
    location: str = ""


class ProposeMeetingUseCase:
    def __init__(
        self,
        meetings: MeetingRepository,
        read_model: StaffMeetingReadModel,
        events: EventDispatcher,
        clock: Clock,
    ) -> None:
        self._meetings = meetings
        self._read = read_model
        self._events = events
        self._clock = clock

    def execute(self, cmd: ProposeCommand) -> StaffMeetingView:
        if cmd.proposed_at <= self._clock():
            raise InvalidSlot("제안 시간은 미래여야 합니다")
        meeting = _load(self._meetings, cmd.meeting_id)
        staff_id = meeting.staff_id or cmd.acting_staff_id
        meeting.propose(
            staff_id=staff_id, proposed_at=cmd.proposed_at, note=cmd.note, location=cmd.location
        )
        self._meetings.save(meeting)
        self._events.publish(
            MeetingProposed(
                meeting_id=meeting.id,
                student_id=meeting.student_id,
                staff_id=staff_id,
                proposed_at=cmd.proposed_at,
            )
        )
        return self._read.get(meeting.id)


@dataclass(frozen=True)
class StaffAvailability:
    slots: list[datetime]
    customized_days: list[date]


def _days(start: datetime, end: datetime) -> tuple[date, date]:
    return start.astimezone(KST).date(), end.astimezone(KST).date()


class GetAvailabilityUseCase:
    def __init__(self, availability: AvailabilityRepository, clock: Clock) -> None:
        self._availability = availability
        self._clock = clock

    def execute(self, staff_id: int, start: datetime, end: datetime) -> StaffAvailability:
        availability_window.ensure_readable(
            *_days(start, end), today=self._clock().astimezone(KST).date()
        )
        return self._read(staff_id, start, end)

    def _read(self, staff_id: int, start: datetime, end: datetime) -> StaffAvailability:
        return StaffAvailability(
            slots=self._availability.for_staff_between(staff_id, start, end),
            customized_days=self._availability.customized_days(staff_id, start, end),
        )


class ResetAvailabilityUseCase:
    """범위의 가능 시간을 직접 설정 이전(기본 가능 시간)으로 되돌린다."""

    def __init__(
        self, availability: AvailabilityRepository, meetings: MeetingRepository, clock: Clock
    ) -> None:
        self._availability = availability
        self._meetings = meetings
        self._clock = clock

    def execute(self, staff_id: int, start: datetime, end: datetime) -> StaffAvailability:
        availability_window.ensure_editable(
            *_days(start, end), today=self._clock().astimezone(KST).date()
        )
        self._availability.reset_to_default(staff_id, start, end)
        result = GetAvailabilityUseCase(self._availability, self._clock)._read(staff_id, start, end)
        # 확정된 면담이 있는 시간은 닫을 수 없다(호출한 쪽 트랜잭션이 롤백한다).
        booked = set(self._meetings.staff_has_confirmed_between(staff_id, start, end))
        if booked - set(result.slots):
            raise SlotHasMeeting("확정된 면담이 있는 시간은 닫을 수 없습니다")
        return result


class SetAvailabilityUseCase:
    """[start, end] 범위의 내 가능 시간을 주어진 목록으로 교체한다."""

    def __init__(
        self, availability: AvailabilityRepository, meetings: MeetingRepository, clock: Clock
    ) -> None:
        self._availability = availability
        self._meetings = meetings
        self._clock = clock

    def execute(
        self, staff_id: int, start: datetime, end: datetime, slots: list[datetime]
    ) -> list[datetime]:
        availability_window.ensure_editable(
            *_days(start, end), today=self._clock().astimezone(KST).date()
        )
        unique = sorted(set(slots))
        for slot in unique:
            if not is_aligned(slot) or not start <= slot <= end:
                raise InvalidSlot("가능 시간은 범위 안의 30분 단위여야 합니다")
        # 확정된 면담이 있는 시간은 닫을 수 없다.
        booked = set(self._meetings.staff_has_confirmed_between(staff_id, start, end))
        if booked - set(unique):
            raise SlotHasMeeting("확정된 면담이 있는 시간은 닫을 수 없습니다")
        self._availability.replace_for_staff(staff_id, start, end, unique)
        return unique


class ListMeetingTypesForStaffUseCase:
    def __init__(self, read_model: StaffMeetingReadModel) -> None:
        self._read = read_model

    def execute(self) -> list[StaffMeetingTypeView]:
        return self._read.list_types()


class SetDefaultStaffUseCase:
    def __init__(
        self,
        types: MeetingTypeRepository,
        directory: StaffDirectory,
        read_model: StaffMeetingReadModel,
    ) -> None:
        self._types = types
        self._directory = directory
        self._read = read_model

    def execute(self, assignments: dict[int, int | None]) -> list[StaffMeetingTypeView]:
        for type_id, staff_id in assignments.items():
            if self._types.get(type_id) is None:
                raise MeetingTypeNotFound("존재하지 않는 면담 유형입니다")
            if staff_id is not None:
                _require_staff(self._directory, staff_id)
        for type_id, staff_id in assignments.items():
            self._types.set_default_staff(type_id, staff_id)
        return self._read.list_types()
