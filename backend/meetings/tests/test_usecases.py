"""유스케이스 테스트: DB 없이 인메모리 구현으로 검증."""

from datetime import UTC, datetime, timedelta

import pytest

from common.domain.errors import ForbiddenError
from common.infrastructure.dispatcher import InProcessEventDispatcher
from meetings.application.ports import MeetingTypeInfo, MeetingView
from meetings.application.usecases import (
    AcceptMeetingProposalUseCase,
    CancelMeetingUseCase,
    RequestMeetingCommand,
    RequestMeetingUseCase,
)
from meetings.domain.errors import (
    InvalidSlot,
    InvalidTransition,
    MeetingNotFound,
    MeetingTypeNotFound,
    SlotUnavailable,
)
from meetings.domain.events import MeetingCanceled, MeetingConfirmed, MeetingRequested
from meetings.domain.meeting import MeetingStatus

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
SLOT = datetime(2026, 10, 13, 15, 0, tzinfo=UTC)
FREEZE = MeetingTypeInfo(id=1, code="freeze", name="프리즈", default_staff_id=9)
OTHER = MeetingTypeInfo(id=2, code="other", name="기타", default_staff_id=None)


class Memory:
    def __init__(self, offered=((9, SLOT),)):
        self.rows = {}
        self.offered = list(offered)

    # MeetingRepository
    def add(self, meeting):
        meeting.id = len(self.rows) + 1
        self.rows[meeting.id] = meeting
        return meeting

    def get(self, meeting_id):
        return self.rows.get(meeting_id)

    def save(self, meeting):
        self.rows[meeting.id] = meeting

    def confirmed_between(self, start, end):
        return [
            (m.staff_id, m.slot_at)
            for m in self.rows.values()
            if m.status == MeetingStatus.CONFIRMED and start <= m.slot_at <= end
        ]

    # AvailabilityRepository
    def offered_between(self, start, end):
        return [(s, t) for s, t in self.offered if start <= t <= end]

    # MeetingTypeRepository
    def get_type(self, type_id):
        return {1: FREEZE, 2: OTHER}.get(type_id)

    # MeetingReadModel
    def get_view(self, meeting_id):
        m = self.rows[meeting_id]
        t = self.get_type(m.type_id)
        return MeetingView(
            m.id,
            t,
            m.slot_at,
            m.content,
            m.notify_slack,
            m.status.value,
            m.staff_id,
            None,
            "",
            None,
        )


class Types:
    def __init__(self, mem):
        self.get = mem.get_type


@pytest.fixture
def env():
    mem = Memory()
    events = []
    bus = InProcessEventDispatcher()
    bus.subscribe(MeetingRequested, events.append)
    bus.subscribe(MeetingCanceled, events.append)
    request = RequestMeetingUseCase(mem, Types(mem), mem, mem, bus, clock=lambda: NOW)
    cancel = CancelMeetingUseCase(mem, mem, bus)
    return mem, events, request, cancel


def cmd(**kw):
    base = dict(student_id=1, type_id=1, slot_at=SLOT, content="문의", notify_slack=True)
    return RequestMeetingCommand(**{**base, **kw})


def test_request_creates_pending_with_default_staff_and_emits_event(env):
    mem, events, request, _ = env
    view = request.execute(cmd())
    assert view.status == "pending" and view.staff_id == 9
    assert isinstance(events[0], MeetingRequested) and events[0].meeting_id == view.id


def test_type_without_default_staff_is_unassigned(env):
    _, _, request, _ = env
    assert request.execute(cmd(type_id=2)).staff_id is None


def test_unknown_type_rejected(env):
    with pytest.raises(MeetingTypeNotFound):
        env[2].execute(cmd(type_id=99))


def test_unaligned_time_rejected(env):
    with pytest.raises(InvalidSlot):
        env[2].execute(cmd(slot_at=SLOT + timedelta(minutes=10)))


def test_unoffered_time_rejected(env):
    with pytest.raises(SlotUnavailable):
        env[2].execute(cmd(slot_at=SLOT + timedelta(hours=1)))


def test_slot_closed_after_confirmed_meeting(env):
    mem, _, request, _ = env
    view = request.execute(cmd())
    mem.rows[view.id].confirm(staff_id=9, location="사무실")
    with pytest.raises(SlotUnavailable):
        request.execute(cmd(student_id=2))


def test_pending_does_not_close_slot(env):
    _, _, request, _ = env
    request.execute(cmd())
    request.execute(cmd(student_id=2))


def test_cancel_by_owner_emits_event(env):
    _, events, request, cancel = env
    view = request.execute(cmd())
    assert cancel.execute(view.id, student_id=1).status == "canceled"
    assert isinstance(events[-1], MeetingCanceled)


def test_cancel_by_other_student_forbidden(env):
    _, _, request, cancel = env
    view = request.execute(cmd())
    with pytest.raises(ForbiddenError):
        cancel.execute(view.id, student_id=2)


def test_cancel_twice_is_invalid_transition(env):
    _, _, request, cancel = env
    view = request.execute(cmd())
    cancel.execute(view.id, 1)
    with pytest.raises(InvalidTransition):
        cancel.execute(view.id, 1)


def test_cancel_unknown_meeting_not_found(env):
    with pytest.raises(MeetingNotFound):
        env[3].execute(404, 1)


def test_accept_publishes_confirmation_event(env, monkeypatch):
    mem, _, request, _ = env
    view = request.execute(cmd())
    mem.rows[view.id].propose(9, SLOT + timedelta(minutes=7))
    monkeypatch.setattr(mem, "has_confirmed", lambda *args, **kwargs: False, raising=False)
    bus = InProcessEventDispatcher()
    events = []
    bus.subscribe(MeetingConfirmed, events.append)
    updated = AcceptMeetingProposalUseCase(mem, mem, bus, lambda: NOW).execute(view.id, 1)
    assert updated.status == "confirmed"
    assert len(events) == 1 and events[0].slot_at == SLOT + timedelta(minutes=7)
