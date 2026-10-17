"""운영 유스케이스 테스트: DB 없이 인메모리 구현."""

import copy
from datetime import UTC, datetime, timedelta

import pytest

from common.infrastructure.dispatcher import InProcessEventDispatcher
from meetings.application.ports import StaffMeetingView, StudentInfo
from meetings.application.staff_usecases import (
    AssignMeetingUseCase,
    ConfirmCommand,
    ConfirmMeetingUseCase,
    ProposeCommand,
    ProposeMeetingUseCase,
    SetAvailabilityUseCase,
)
from meetings.domain.errors import (
    InvalidSlot,
    InvalidTransition,
    SlotHasMeeting,
    SlotUnavailable,
    StaffNotFound,
)
from meetings.domain.events import MeetingConfirmed, MeetingProposed
from meetings.domain.meeting import MeetingRequest, MeetingStatus

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
T = datetime(2026, 10, 13, 15, 0, tzinfo=UTC)


class Memory:
    def __init__(self):
        self.rows: dict[int, MeetingRequest] = {}
        self.staff_ids = {9, 10}
        self.availability: dict[int, set] = {}

    def add(self, **kw):
        m = MeetingRequest(student_id=1, type_id=1, slot_at=T, content="c", **kw)
        m.id = len(self.rows) + 1
        self.rows[m.id] = copy.copy(m)
        return m

    def get(self, meeting_id):
        row = self.rows.get(meeting_id)
        return copy.copy(row) if row else None  # 저장소처럼 매번 새 객체를 돌려준다

    def save(self, meeting):
        self.rows[meeting.id] = copy.copy(meeting)

    def has_confirmed(self, staff_id, at, exclude_id):
        return any(
            m.status == MeetingStatus.CONFIRMED
            and m.staff_id == staff_id
            and m.slot_at == at
            and m.id != exclude_id
            for m in self.rows.values()
        )

    def staff_has_confirmed_between(self, staff_id, start, end):
        return [
            m.slot_at
            for m in self.rows.values()
            if m.status == MeetingStatus.CONFIRMED
            and m.staff_id == staff_id
            and start <= m.slot_at <= end
        ]

    def is_staff(self, user_id):
        return user_id in self.staff_ids

    def get_view(self, meeting_id):  # StaffMeetingReadModel.get 대체용
        return StaffMeetingView(None, StudentInfo(1, "s", "s"), "", NOW)

    def replace_for_staff(self, staff_id, start, end, slots):
        self.availability[staff_id] = set(slots)


class Read:
    def __init__(self, mem):
        self.get = lambda meeting_id: mem.get_view(meeting_id)


@pytest.fixture
def env():
    mem = Memory()
    events = []
    bus = InProcessEventDispatcher()
    bus.subscribe(MeetingConfirmed, events.append)
    bus.subscribe(MeetingProposed, events.append)
    return mem, Read(mem), bus, events


def confirm_uc(env):
    mem, read, bus, _ = env
    return ConfirmMeetingUseCase(mem, mem, read, bus)


def test_confirm_sets_location_staff_and_emits_event(env):
    mem, *_, events = env
    m = mem.add()
    confirm_uc(env).execute(ConfirmCommand(m.id, acting_staff_id=9, location="1층"))
    m = mem.rows[m.id]
    assert (m.status, m.staff_id, m.location) == (MeetingStatus.CONFIRMED, 9, "1층")
    assert isinstance(events[0], MeetingConfirmed) and events[0].location == "1층"


def test_confirm_uses_assigned_staff_over_acting(env):
    mem = env[0]
    m = mem.add(staff_id=10)
    confirm_uc(env).execute(ConfirmCommand(m.id, acting_staff_id=9, location="x"))
    assert mem.rows[m.id].staff_id == 10


def test_double_confirm_same_staff_same_time_blocked(env):
    mem, *_ = env
    first, second = mem.add(), mem.add()
    uc = confirm_uc(env)
    uc.execute(ConfirmCommand(first.id, 9, "a"))
    with pytest.raises(SlotUnavailable):
        uc.execute(ConfirmCommand(second.id, 9, "b"))
    assert mem.rows[second.id].status == MeetingStatus.PENDING  # 저장되지 않음


def test_same_time_different_staff_allowed(env):
    mem, *_ = env
    first, second = mem.add(), mem.add()
    uc = confirm_uc(env)
    uc.execute(ConfirmCommand(first.id, 9, "a"))
    uc.execute(ConfirmCommand(second.id, 9, "b", staff_id=10))
    assert mem.rows[second.id].staff_id == 10


def test_confirm_non_staff_rejected(env):
    m = env[0].add()
    with pytest.raises(StaffNotFound):
        confirm_uc(env).execute(ConfirmCommand(m.id, 9, "x", staff_id=999))


def test_confirm_twice_invalid_transition(env):
    m = env[0].add()
    uc = confirm_uc(env)
    uc.execute(ConfirmCommand(m.id, 9, "x"))
    with pytest.raises(InvalidTransition):
        uc.execute(ConfirmCommand(m.id, 9, "x"))


def test_propose_sets_time_and_emits_event(env):
    mem, read, bus, events = env
    m = mem.add()
    later = T + timedelta(hours=1, minutes=7)
    ProposeMeetingUseCase(mem, read, bus, clock=lambda: NOW).execute(
        ProposeCommand(m.id, 9, later, "다른 시간 어떠세요")
    )
    m = mem.rows[m.id]
    assert m.status == MeetingStatus.PROPOSED and m.proposed_at == later
    assert isinstance(events[0], MeetingProposed)


@pytest.mark.parametrize("bad", [NOW, NOW - timedelta(days=1)])
def test_propose_rejects_present_or_past(env, bad):
    mem, read, bus, _ = env
    m = mem.add()
    with pytest.raises(InvalidSlot):
        ProposeMeetingUseCase(mem, read, bus, clock=lambda: NOW).execute(
            ProposeCommand(m.id, 9, bad)
        )


def test_assign_requires_staff_account(env):
    mem, read, *_ = env
    m = mem.add()
    uc = AssignMeetingUseCase(mem, mem, read)
    uc.execute(m.id, 10)
    assert mem.rows[m.id].staff_id == 10
    with pytest.raises(StaffNotFound):
        uc.execute(m.id, 1)


def test_set_availability_validates_and_protects_confirmed(env):
    mem, *_ = env
    uc = SetAvailabilityUseCase(mem, mem)
    start, end = T - timedelta(hours=1), T + timedelta(hours=3)
    with pytest.raises(InvalidSlot):
        uc.execute(9, start, end, [T + timedelta(minutes=10)])
    with pytest.raises(InvalidSlot):
        uc.execute(9, start, end, [end + timedelta(hours=1)])
    assert uc.execute(9, start, end, [T, T, T + timedelta(minutes=30)]) == [
        T,
        T + timedelta(minutes=30),
    ]
    mem.add(staff_id=9, status=MeetingStatus.CONFIRMED)
    assert mem.availability[9] == {T, T + timedelta(minutes=30)}
    with pytest.raises(SlotHasMeeting):
        uc.execute(9, start, end, [T + timedelta(minutes=30)])
    uc.execute(9, start, end, [T])  # 확정 시간은 유지하면 OK
