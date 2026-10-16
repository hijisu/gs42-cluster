"""운영 유스케이스 테스트: DB 없이 인메모리 구현."""

import copy
from datetime import datetime

import pytest

from common.infrastructure.dispatcher import InProcessEventDispatcher
from rooms.application.ports import ReservationView, RoomInfo, StaffReservationRow, UserInfo
from rooms.application.staff_usecases import (
    ApproveReservationUseCase,
    ListStaffReservationsUseCase,
    ReassignReservationUseCase,
    RejectReservationUseCase,
    StaffBookingCommand,
    StaffBookUseCase,
)
from rooms.domain.errors import (
    InvalidTransition,
    OutsideHours,
    ReasonRequired,
    ReservationNotFound,
    RoomBlocked,
    RoomConflict,
    RoomNotFound,
)
from rooms.domain.events import ReservationApproved, ReservationReassigned, ReservationRejected
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.rules import DEFAULT_RULES, KST
from rooms.domain.time_range import TimeRange

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=KST)
ROOMS = {
    1: RoomInfo(1, "multipurpose", "다목적회의실", "", "TV", "open"),
    2: RoomInfo(2, "universe-small", "유니버스룸(소)", "", "TV", "open"),
    3: RoomInfo(3, "closed", "차단", "", "", "blocked"),
}


def at(hour, day=13):
    return datetime(2026, 10, day, hour, tzinfo=KST)


class Store:
    """RoomRepository + ReservationRepository + ReadModel 인메모리 구현."""

    def __init__(self):
        self.rows: dict[int, RoomReservation] = {}
        self.locked: list[int] = []

    # RoomRepository
    def get_room(self, room_id):
        return ROOMS.get(room_id)

    # ReservationRepository
    def add(self, r):
        r.id = len(self.rows) + 1
        self.rows[r.id] = copy.copy(r)
        return r

    def get(self, reservation_id):
        row = self.rows.get(reservation_id)
        return copy.copy(row) if row else None

    def save(self, r):
        self.rows[r.id] = copy.copy(r)

    def lock_room(self, room_id):
        self.locked.append(room_id)

    def active_between(self, start, end):
        return [
            copy.copy(r)
            for r in self.rows.values()
            if r.is_active and r.time_range.start < end and r.time_range.end > start
        ]

    # ReadModel
    def _row(self, r):
        view = ReservationView(
            r.id,
            ROOMS[r.room_id],
            ROOMS[r.requested_room_id],
            r.time_range.start,
            r.time_range.end,
            r.purpose,
            r.headcount,
            r.note,
            r.status.value,
            r.reject_reason,
        )
        return StaffReservationRow(
            copy.copy(r), view, UserInfo(r.user_id, f"u{r.user_id}", f"사용자{r.user_id}")
        )

    def get_for_staff(self, reservation_id):
        if reservation_id not in self.rows:
            raise ReservationNotFound("x")
        return self._row(self.rows[reservation_id])

    def list_for_staff(self, start, end, status):
        return [
            self._row(r)
            for r in sorted(self.rows.values(), key=lambda r: (r.time_range.start, r.id))
            if r.time_range.start < end
            and r.time_range.end > start
            and (not status or r.status.value == status)
        ]


class Rooms:
    def __init__(self, store):
        self.get = store.get_room


@pytest.fixture
def env():
    store, events = Store(), []
    bus = InProcessEventDispatcher()
    for event_type in (ReservationApproved, ReservationRejected, ReservationReassigned):
        bus.subscribe(event_type, events.append)
    return store, events, bus


def add(store, user=1, room=1, start=14, end=16, status=ReservationStatus.PENDING, day=13):
    r = RoomReservation(
        user_id=user,
        room_id=room,
        time_range=TimeRange(at(start, day), at(end, day)),
        purpose="회의",
        headcount=3,
        status=status,
    )
    return store.add(r)


def make(cls, env, *extra):
    store, _, bus = env
    return (
        cls(Rooms(store), store, store, *extra)
        if cls is ListStaffReservationsUseCase
        else cls(Rooms(store), store, store, bus, *extra)
    )


def test_approve_locks_room_sets_status_and_emits_event(env):
    store, events, _ = env
    r = add(store)
    view = make(ApproveReservationUseCase, env).execute(r.id)
    assert view.view.status == "approved" and store.locked == [1]
    assert isinstance(events[0], ReservationApproved) and events[0].user_id == 1


def test_second_overlapping_approval_is_blocked_and_stays_pending(env):
    store, events, _ = env
    first, second = add(store, user=1), add(store, user=2, start=15, end=17)
    uc = make(ApproveReservationUseCase, env)
    uc.execute(first.id)
    with pytest.raises(RoomConflict):
        uc.execute(second.id)
    assert store.rows[second.id].status == ReservationStatus.PENDING and len(events) == 1


def test_adjacent_reservations_can_both_be_approved(env):
    store, *_ = env
    a, b = add(store, start=14, end=16), add(store, user=2, start=16, end=18)
    uc = make(ApproveReservationUseCase, env)
    uc.execute(a.id)
    uc.execute(b.id)


def test_overlapping_in_other_room_can_both_be_approved(env):
    store, *_ = env
    a, b = add(store), add(store, user=2, room=2)
    uc = make(ApproveReservationUseCase, env)
    uc.execute(a.id)
    uc.execute(b.id)


def test_approve_unknown_blocked_room_and_wrong_state(env):
    store, *_ = env
    uc = make(ApproveReservationUseCase, env)
    with pytest.raises(ReservationNotFound):
        uc.execute(99)
    with pytest.raises(RoomBlocked):
        uc.execute(add(store, room=3).id)
    done = add(store, status=ReservationStatus.REJECTED)
    with pytest.raises(InvalidTransition):
        uc.execute(done.id)


def test_reject_records_reason_and_emits_event(env):
    store, events, _ = env
    r = add(store)
    view = make(RejectReservationUseCase, env).execute(r.id, "해당 시간 기존 예약")
    assert (view.view.status, view.view.reject_reason) == ("rejected", "해당 시간 기존 예약")
    assert isinstance(events[0], ReservationRejected) and events[0].reason == "해당 시간 기존 예약"


def test_reject_needs_reason_and_pending_state(env):
    store, events, _ = env
    r = add(store)
    uc = make(RejectReservationUseCase, env)
    with pytest.raises(ReasonRequired):
        uc.execute(r.id, " ")
    uc.execute(r.id, "사유")
    with pytest.raises(InvalidTransition):
        uc.execute(r.id, "again")
    assert len(events) == 1


def test_reassign_moves_room_approves_and_keeps_requested_room(env):
    store, events, _ = env
    r = add(store, room=1)
    view = make(ReassignReservationUseCase, env).execute(r.id, 2)
    assert (view.view.room.id, view.view.requested_room.id, view.view.status) == (2, 1, "approved")
    event = events[0]
    assert isinstance(event, ReservationReassigned) and (event.from_room_id, event.to_room_id) == (
        1,
        2,
    )
    assert store.locked == [2]  # 새 장소를 잠근다


def test_reassign_conflict_in_new_room_leaves_reservation_untouched(env):
    store, events, _ = env
    other = add(store, user=2, room=2, status=ReservationStatus.APPROVED)
    r = add(store, room=1)
    with pytest.raises(RoomConflict):
        make(ReassignReservationUseCase, env).execute(r.id, 2)
    assert (store.rows[r.id].room_id, store.rows[r.id].status) == (1, ReservationStatus.PENDING)
    assert other.id and events == []


def test_reassign_to_unknown_or_blocked_room(env):
    store, *_ = env
    r = add(store)
    uc = make(ReassignReservationUseCase, env)
    with pytest.raises(RoomNotFound):
        uc.execute(r.id, 99)
    with pytest.raises(RoomBlocked):
        uc.execute(r.id, 3)


def book(env, **kw):
    store, _, bus = env
    base = dict(
        staff_id=100, room_id=1, start_at=at(14), end_at=at(16), purpose="교육", headcount=10
    )
    uc = StaffBookUseCase(Rooms(store), store, store, bus, lambda: NOW, lambda: DEFAULT_RULES)
    return uc.execute(StaffBookingCommand(**{**base, **kw}))


def test_staff_booking_is_approved_immediately_and_marked(env):
    store, events, _ = env
    view = book(env)
    assert view.view.status == "approved" and view.created_by_staff is True and view.user.id == 100
    assert events == []  # 본인 예약은 알리지 않는다


def test_staff_booking_for_a_student_notifies_them(env):
    _, events, _ = env
    book(env, user_id=7)
    assert isinstance(events[0], ReservationApproved) and events[0].user_id == 7


def test_staff_booking_conflict_and_rules(env):
    store, *_ = env
    add(store, status=ReservationStatus.APPROVED)
    with pytest.raises(RoomConflict):
        book(env)
    with pytest.raises(OutsideHours):
        book(env, start_at=at(7), end_at=at(8))
    with pytest.raises(RoomBlocked):
        book(env, room_id=3)


def test_list_flags_pending_conflicts_with_ids_only_for_pending(env):
    store, _, bus = env
    approved = add(store, user=1, status=ReservationStatus.APPROVED)
    pending = add(store, user=2, start=15, end=17)
    lonely = add(store, user=3, room=2)
    uc = ListStaffReservationsUseCase(Rooms(store), store, store, lambda: NOW)
    rows = {v.view.id: v for v in uc.execute(None, None)}
    assert rows[pending.id].conflict_ids == [approved.id] and rows[pending.id].view.conflict is True
    assert rows[approved.id].conflict_ids == [] and rows[lonely.id].view.conflict is False
    assert bus  # 사용 안 함 방지용


def test_list_filters_by_date_and_status_and_defaults_to_upcoming(env):
    store, *_ = env
    today = add(store, day=13)
    add(store, day=14, status=ReservationStatus.APPROVED)
    add(store, day=1)  # 과거
    uc = ListStaffReservationsUseCase(Rooms(store), store, store, lambda: NOW)
    from datetime import date

    assert [v.view.id for v in uc.execute(date(2026, 10, 13), None)] == [today.id]
    assert [v.view.status for v in uc.execute(date(2026, 10, 14), "approved")] == ["approved"]
    assert uc.execute(date(2026, 10, 14), "pending") == []
    assert len(uc.execute(None, None)) == 2  # 오늘(10/12) 이후만
