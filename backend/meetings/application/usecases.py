from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from common.domain.events import EventDispatcher
from meetings.application.ports import (
    AvailabilityRepository,
    MeetingReadModel,
    MeetingRepository,
    MeetingTypeInfo,
    MeetingTypeRepository,
    MeetingView,
)
from meetings.domain.defaults import default_slots
from meetings.domain.errors import (
    InvalidSlot,
    MeetingNotFound,
    MeetingTypeNotFound,
    SlotUnavailable,
)
from meetings.domain.events import MeetingCanceled, MeetingConfirmed, MeetingRequested
from meetings.domain.meeting import MeetingRequest
from meetings.domain.slots import SlotAvailability, compute_slots, is_aligned

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class RequestMeetingCommand:
    student_id: int
    type_id: int
    slot_at: datetime
    content: str
    notify_slack: bool = False


class GetSlotsUseCase:
    def __init__(
        self, availability: AvailabilityRepository, meetings: MeetingRepository, clock: Clock
    ) -> None:
        self._availability = availability
        self._meetings = meetings
        self._clock = clock

    def execute(
        self, start: datetime, end: datetime, staff_id: int | None = None
    ) -> list[SlotAvailability]:
        """평일 운영 시간 전체(+운영 시간 밖에 누가 연 시간)를 시간순으로 돌려준다.

        각 칸의 state: open(신청 가능) / full(마감) / unavailable(불가: 연 담당자 없음).
        staff_id 를 주면 그 담당자가 연 시간·확정 면담만으로 계산한다(유형별 기본 담당자 기준).
        담당자가 정해지지 않은 확정 면담은 누구의 자리든 1자리를 차지하므로 그대로 반영한다.
        """
        offered = self._availability.offered_between(start, end)
        confirmed = self._meetings.confirmed_between(start, end)
        if staff_id is not None:
            offered = [(who, at) for who, at in offered if who == staff_id]
            confirmed = [(who, at) for who, at in confirmed if who in (staff_id, None)]
        grid = {s.start_at: s for s in compute_slots(offered, confirmed, now=self._clock())}
        for at in default_slots(start, end):
            grid.setdefault(at, SlotAvailability(start_at=at, remaining=0, offered=0))
        return [grid[key] for key in sorted(grid)]


class RequestMeetingUseCase:
    def __init__(
        self,
        meetings: MeetingRepository,
        types: MeetingTypeRepository,
        availability: AvailabilityRepository,
        read_model: MeetingReadModel,
        events: EventDispatcher,
        clock: Clock,
    ) -> None:
        self._meetings = meetings
        self._types = types
        self._availability = availability
        self._read = read_model
        self._events = events
        self._clock = clock

    def execute(self, cmd: RequestMeetingCommand) -> MeetingView:
        meeting_type: MeetingTypeInfo | None = self._types.get(cmd.type_id)
        if meeting_type is None:
            raise MeetingTypeNotFound("존재하지 않는 면담 유형입니다")
        if not is_aligned(cmd.slot_at):
            raise InvalidSlot("면담 시간은 30분 단위여야 합니다")

        slots = GetSlotsUseCase(self._availability, self._meetings, self._clock).execute(
            cmd.slot_at, cmd.slot_at, staff_id=meeting_type.default_staff_id
        )
        if not any(s.start_at == cmd.slot_at and s.available for s in slots):
            raise SlotUnavailable("선택한 시간은 마감되었거나 열려 있지 않습니다")

        meeting = self._meetings.add(
            MeetingRequest(
                student_id=cmd.student_id,
                type_id=meeting_type.id,
                slot_at=cmd.slot_at,
                content=cmd.content,
                notify_slack=cmd.notify_slack,
                staff_id=meeting_type.default_staff_id,
            )
        )
        self._events.publish(
            MeetingRequested(
                meeting_id=meeting.id,
                student_id=meeting.student_id,
                type_id=meeting.type_id,
                slot_at=meeting.slot_at,
                staff_id=meeting.staff_id,
            )
        )
        return self._read.get_view(meeting.id)


class CancelMeetingUseCase:
    def __init__(
        self, meetings: MeetingRepository, read_model: MeetingReadModel, events: EventDispatcher
    ) -> None:
        self._meetings = meetings
        self._read = read_model
        self._events = events

    def execute(self, meeting_id: int, student_id: int) -> MeetingView:
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise MeetingNotFound("면담을 찾을 수 없습니다")
        meeting.cancel(by_student_id=student_id)
        self._meetings.save(meeting)
        self._events.publish(
            MeetingCanceled(
                meeting_id=meeting.id, student_id=meeting.student_id, staff_id=meeting.staff_id
            )
        )
        return self._read.get_view(meeting.id)


class ListMyMeetingsUseCase:
    def __init__(self, read_model: MeetingReadModel) -> None:
        self._read = read_model

    def execute(self, student_id: int) -> list[MeetingView]:
        return self._read.list_for_student(student_id)


class AcceptMeetingProposalUseCase:
    def __init__(
        self,
        meetings: MeetingRepository,
        read_model: MeetingReadModel,
        events: EventDispatcher,
        clock: Clock,
    ) -> None:
        self._meetings, self._read, self._events, self._clock = meetings, read_model, events, clock

    def execute(self, meeting_id: int, student_id: int) -> MeetingView:
        meeting = self._meetings.get(meeting_id)
        if meeting is None:
            raise MeetingNotFound("면담을 찾을 수 없습니다")
        meeting.accept_proposal(student_id, self._clock())
        if self._meetings.has_confirmed(meeting.staff_id, meeting.slot_at, exclude_id=meeting.id):
            raise SlotUnavailable("같은 담당자의 같은 시간에 이미 확정된 면담이 있습니다")
        self._meetings.save(meeting)
        self._events.publish(
            MeetingConfirmed(
                meeting_id=meeting.id,
                student_id=meeting.student_id,
                staff_id=meeting.staff_id,
                slot_at=meeting.slot_at,
                location=meeting.location,
            )
        )
        return self._read.get_view(meeting.id)
