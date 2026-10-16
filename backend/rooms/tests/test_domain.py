"""도메인 테스트: DB 없이 실행."""

from datetime import datetime, timedelta

import pytest

from common.domain.errors import ForbiddenError
from rooms.domain.conflict import ConflictChecker
from rooms.domain.errors import (
    InvalidRange,
    InvalidTransition,
    OutsideHours,
    PastTime,
    RoomConflict,
)
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.rules import DEFAULT_RULES, KST
from rooms.domain.time_range import TimeRange

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=KST)


def at(hour, minute=0, day=13):
    return datetime(2026, 10, day, hour, minute, tzinfo=KST)


def rng(start_h, end_h, day=13):
    return TimeRange(at(start_h, day=day), at(end_h, day=day))


def res(start_h=14, end_h=16, room=1, user=1, status=ReservationStatus.PENDING, id=None):
    return RoomReservation(
        user_id=user,
        room_id=room,
        time_range=rng(start_h, end_h),
        purpose="회의",
        headcount=3,
        status=status,
        id=id,
    )


# ── TimeRange ──
def test_range_requires_end_after_start():
    with pytest.raises(InvalidRange):
        TimeRange(at(10), at(10))
    with pytest.raises(InvalidRange):
        TimeRange(at(11), at(10))


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ((10, 12), (11, 13), True),
        ((10, 12), (12, 14), False),  # 맞닿음은 겹침이 아님
        ((10, 14), (11, 12), True),  # 포함
        ((10, 11), (12, 13), False),
        ((12, 14), (10, 13), True),
    ],
)
def test_overlaps(a, b, expected):
    assert rng(*a).overlaps(rng(*b)) is expected
    assert rng(*b).overlaps(rng(*a)) is expected


# ── RoomRules ──
def test_rules_accept_valid_request():
    DEFAULT_RULES.validate(rng(9, 22), NOW)
    DEFAULT_RULES.validate(TimeRange(at(13, 30), at(14, 30)), NOW)


def test_rules_reject_past_start():
    with pytest.raises(PastTime):
        DEFAULT_RULES.validate(rng(10, 11, day=11), NOW)


@pytest.mark.parametrize("start,end", [(8, 10), (21, 23), (6, 7)])
def test_rules_reject_outside_operating_hours(start, end):
    with pytest.raises(OutsideHours):
        DEFAULT_RULES.validate(rng(start, end), NOW)


def test_rules_reject_range_crossing_midnight():
    crossing = TimeRange(at(21), at(10, day=14))
    with pytest.raises(OutsideHours):
        DEFAULT_RULES.validate(crossing, NOW)


def test_rules_reject_non_30_minute_steps():
    with pytest.raises(InvalidRange):
        DEFAULT_RULES.validate(TimeRange(at(10, 15), at(11)), NOW)


def test_rules_hours_are_evaluated_in_kst_regardless_of_input_tz():
    # 01:00 UTC = 10:00 KST → 운영시간 안
    from datetime import UTC

    DEFAULT_RULES.validate(
        TimeRange(datetime(2026, 10, 13, 1, tzinfo=UTC), datetime(2026, 10, 13, 2, tzinfo=UTC)), NOW
    )


# ── RoomReservation ──
def test_new_reservation_is_pending_and_remembers_requested_room():
    r = res(room=2)
    assert r.status == ReservationStatus.PENDING and r.requested_room_id == 2


def test_approve_and_reject_only_from_pending():
    r = res()
    r.approve()
    assert r.status == ReservationStatus.APPROVED
    for action in (r.approve, lambda: r.reject("x")):
        with pytest.raises(InvalidTransition):
            action()


def test_reject_records_reason():
    r = res()
    r.reject("기존 예약")
    assert (r.status, r.reject_reason) == (ReservationStatus.REJECTED, "기존 예약")


def test_reassign_changes_room_but_keeps_requested_room():
    r = res(room=1)
    r.reassign(3)
    assert (r.room_id, r.requested_room_id) == (3, 1)


@pytest.mark.parametrize("terminal", [ReservationStatus.REJECTED, ReservationStatus.CANCELED])
def test_terminal_states_reject_everything(terminal):
    for action in (
        lambda r: r.approve(),
        lambda r: r.reject("x"),
        lambda r: r.reassign(2),
        lambda r: r.cancel(1),
    ):
        with pytest.raises(InvalidTransition):
            action(res(status=terminal))


@pytest.mark.parametrize("status", [ReservationStatus.PENDING, ReservationStatus.APPROVED])
def test_owner_can_cancel_active(status):
    r = res(status=status)
    r.cancel(by_user_id=1)
    assert r.status == ReservationStatus.CANCELED


def test_only_owner_can_cancel():
    r = res()
    with pytest.raises(ForbiddenError):
        r.cancel(by_user_id=2)
    assert r.status == ReservationStatus.PENDING


# ── ConflictChecker ──
def test_conflict_same_room_overlap():
    target = res(14, 16, id=1)
    assert ConflictChecker.has_conflict(target, [res(15, 17, id=2)])


def test_no_conflict_when_adjacent_other_room_or_inactive():
    target = res(14, 16, id=1)
    assert not ConflictChecker.has_conflict(target, [res(16, 18, id=2)])
    assert not ConflictChecker.has_conflict(target, [res(14, 16, room=2, id=3)])
    assert not ConflictChecker.has_conflict(
        target, [res(14, 16, id=4, status=ReservationStatus.REJECTED)]
    )
    assert not ConflictChecker.has_conflict(
        target, [res(14, 16, id=5, status=ReservationStatus.CANCELED)]
    )


def test_target_does_not_conflict_with_itself():
    target = res(14, 16, id=1)
    assert ConflictChecker.conflicts(target, [target]) == []


def test_pending_overlaps_are_allowed_to_approve_until_one_is_approved():
    a, b = res(14, 16, id=1), res(15, 17, id=2)
    ConflictChecker.ensure_can_approve(a, [b])  # 대기끼리는 통과
    b.approve()
    with pytest.raises(RoomConflict):
        ConflictChecker.ensure_can_approve(a, [b])


def test_duration():
    assert rng(10, 12).duration == timedelta(hours=2)
