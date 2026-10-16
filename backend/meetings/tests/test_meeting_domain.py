"""도메인 테스트: DB 없이 실행."""

from datetime import UTC, datetime, timedelta

import pytest

from common.domain.errors import ForbiddenError
from meetings.domain.errors import InvalidTransition
from meetings.domain.meeting import MeetingRequest, MeetingStatus
from meetings.domain.slots import compute_slots, is_aligned

T = datetime(2026, 10, 13, 15, 0, tzinfo=UTC)


def new_meeting(**kw):
    return MeetingRequest(student_id=1, type_id=1, slot_at=T, content="문의", **kw)


def test_new_meeting_is_pending():
    assert new_meeting().status == MeetingStatus.PENDING


def test_pending_to_confirmed_to_completed():
    m = new_meeting()
    m.confirm(staff_id=9, location="1층 사무실 앞")
    assert (m.status, m.staff_id, m.location) == (MeetingStatus.CONFIRMED, 9, "1층 사무실 앞")
    m.complete()
    assert m.status == MeetingStatus.COMPLETED


def test_propose_then_confirm_uses_proposed_time():
    m = new_meeting()
    later = T + timedelta(hours=2)
    m.propose(staff_id=9, proposed_at=later)
    assert m.status == MeetingStatus.PROPOSED
    m.confirm(staff_id=9, location="회의실")
    assert m.slot_at == later


@pytest.mark.parametrize("terminal", [MeetingStatus.COMPLETED, MeetingStatus.CANCELED])
def test_terminal_states_reject_all_transitions(terminal):
    for action in (
        lambda m: m.confirm(9, "x"),
        lambda m: m.propose(9, T),
        lambda m: m.complete(),
        lambda m: m.cancel(1),
    ):
        m = new_meeting(status=terminal)
        with pytest.raises(InvalidTransition):
            action(m)


def test_complete_requires_confirmed():
    with pytest.raises(InvalidTransition):
        new_meeting().complete()


@pytest.mark.parametrize(
    "status", [MeetingStatus.PENDING, MeetingStatus.PROPOSED, MeetingStatus.CONFIRMED]
)
def test_owner_can_cancel_active_meeting(status):
    m = new_meeting(status=status)
    m.cancel(by_student_id=1)
    assert m.status == MeetingStatus.CANCELED


def test_non_owner_cannot_cancel():
    m = new_meeting()
    with pytest.raises(ForbiddenError):
        m.cancel(by_student_id=2)
    assert m.status == MeetingStatus.PENDING


def test_is_aligned():
    assert is_aligned(T) and is_aligned(T + timedelta(minutes=30))
    assert not is_aligned(T + timedelta(minutes=15))
    assert not is_aligned(T + timedelta(seconds=1))


NOW = T - timedelta(days=1)


def test_slot_open_when_staff_offers_and_no_confirmed():
    (slot,) = compute_slots([(1, T)], [], NOW)
    assert slot.available and slot.remaining == 1


def test_confirmed_meeting_closes_that_staffs_slot():
    (slot,) = compute_slots([(1, T)], [(1, T)], NOW)
    assert not slot.available


def test_other_staff_keeps_slot_open():
    (slot,) = compute_slots([(1, T), (2, T)], [(1, T)], NOW)
    assert slot.remaining == 1


def test_unassigned_confirmed_takes_one_seat():
    (slot,) = compute_slots([(1, T)], [(None, T)], NOW)
    assert not slot.available


def test_past_slots_are_closed():
    (slot,) = compute_slots([(1, T)], [], now=T + timedelta(minutes=1))
    assert not slot.available


def test_slots_sorted_by_time_and_unoffered_times_absent():
    result = compute_slots([(1, T + timedelta(hours=1)), (1, T)], [], NOW)
    assert [s.start_at for s in result] == [T, T + timedelta(hours=1)]
