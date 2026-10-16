"""유스케이스 테스트: DB 없이 인메모리 구현."""

import copy
from datetime import date, datetime

import pytest

from common.domain.errors import ForbiddenError
from common.infrastructure.dispatcher import InProcessEventDispatcher
from rooms.application.ports import ReservationView, RoomInfo
from rooms.application.usecases import (
    CancelReservationUseCase,
    GetAvailabilityUseCase,
    ListMyReservationsUseCase,
    RequestReservationCommand,
    RequestReservationUseCase,
)
from rooms.domain.errors import (
    InvalidRange,
    OutsideHours,
    PastTime,
    ReservationNotFound,
    RoomBlocked,
    RoomNotFound,
)
from rooms.domain.events import ReservationCanceled, ReservationRequested
from rooms.domain.rules import KST

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=KST)
ROOMS = {
    1: RoomInfo(1, "multipurpose", "다목적회의실", "", "TV", "open"),
    2: RoomInfo(2, "universe-small", "유니버스룸(소)", "", "TV", "open"),
    3: RoomInfo(3, "closed", "차단된 방", "", "", "blocked"),
}


def at(hour, minute=0, day=13):
    return datetime(2026, 10, day, hour, minute, tzinfo=KST)


class Rooms:
    def list_all(self):
        return list(ROOMS.values())

    def get(self, room_id):
        return ROOMS.get(room_id)


class Store:
    def __init__(self):
        self.rows = {}

    def add(self, reservation):
        reservation.id = len(self.rows) + 1
        self.rows[reservation.id] = copy.copy(reservation)
        return reservation

    def get(self, reservation_id):
        row = self.rows.get(reservation_id)
        return copy.copy(row) if row else None

    def save(self, reservation):
        self.rows[reservation.id] = copy.copy(reservation)

    def active_between(self, start, end):
        return [
            copy.copy(r)
            for r in self.rows.values()
            if r.is_active and r.time_range.start < end and r.time_range.end > start
        ]


class Read:
    def __init__(self, store):
        self.store = store

    def _view(self, r):
        return ReservationView(
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

    def get_view(self, reservation_id):
        return self._view(self.store.rows[reservation_id])

    def list_for_user(self, user_id):
        return [self._view(r) for r in self.store.rows.values() if r.user_id == user_id]


@pytest.fixture
def env():
    store, events = Store(), []
    bus = InProcessEventDispatcher()
    bus.subscribe(ReservationRequested, events.append)
    bus.subscribe(ReservationCanceled, events.append)
    read = Read(store)
    request = RequestReservationUseCase(Rooms(), store, read, bus, clock=lambda: NOW)
    cancel = CancelReservationUseCase(store, read, bus)
    return store, events, request, cancel, read


def cmd(**kw):
    base = dict(user_id=1, room_id=1, start_at=at(14), end_at=at(16), purpose="회의", headcount=3)
    return RequestReservationCommand(**{**base, **kw})


def test_request_creates_pending_and_emits_event(env):
    _, events, request, *_ = env
    view = request.execute(cmd())
    assert view.status == "pending" and view.conflict is False
    assert isinstance(events[0], ReservationRequested)


def test_overlapping_pending_is_accepted_but_flagged(env):
    _, _, request, *_ = env
    request.execute(cmd(user_id=1))
    second = request.execute(cmd(user_id=2, start_at=at(15), end_at=at(17)))
    assert second.status == "pending" and second.conflict is True


def test_overlap_with_approved_is_flagged(env):
    store, _, request, *_ = env
    first = request.execute(cmd(user_id=1))
    store.rows[first.id].approve()
    assert request.execute(cmd(user_id=2)).conflict is True


def test_other_room_same_time_not_flagged(env):
    _, _, request, *_ = env
    request.execute(cmd())
    assert request.execute(cmd(user_id=2, room_id=2)).conflict is False


def test_adjacent_not_flagged(env):
    _, _, request, *_ = env
    request.execute(cmd())
    assert request.execute(cmd(user_id=2, start_at=at(16), end_at=at(17))).conflict is False


@pytest.mark.parametrize(
    ("kw", "error"),
    [
        (dict(room_id=99), RoomNotFound),
        (dict(room_id=3), RoomBlocked),
        (dict(start_at=at(10, day=11), end_at=at(11, day=11)), PastTime),
        (dict(start_at=at(8), end_at=at(10)), OutsideHours),
        (dict(start_at=at(21), end_at=at(23)), OutsideHours),
        (dict(start_at=at(16), end_at=at(15)), InvalidRange),
        (dict(start_at=at(14, 10), end_at=at(15)), InvalidRange),
    ],
)
def test_invalid_requests_are_rejected_and_nothing_is_saved(env, kw, error):
    store, _, request, *_ = env
    with pytest.raises(error):
        request.execute(cmd(**kw))
    assert store.rows == {}


def test_cancel_by_owner(env):
    _, events, request, cancel, _ = env
    view = request.execute(cmd())
    assert cancel.execute(view.id, 1).status == "canceled"
    assert isinstance(events[-1], ReservationCanceled)


def test_cancel_by_other_forbidden_and_unknown_not_found(env):
    _, _, request, cancel, _ = env
    view = request.execute(cmd())
    with pytest.raises(ForbiddenError):
        cancel.execute(view.id, 2)
    with pytest.raises(ReservationNotFound):
        cancel.execute(999, 1)


def test_canceled_reservation_no_longer_conflicts(env):
    _, _, request, cancel, _ = env
    first = request.execute(cmd(user_id=1))
    cancel.execute(first.id, 1)
    assert request.execute(cmd(user_id=2)).conflict is False


def test_my_reservations_flags_conflicting_pending_only(env):
    store, _, request, _, read = env
    request.execute(cmd(user_id=1))
    request.execute(cmd(user_id=2))
    views = ListMyReservationsUseCase(store, read).execute(2)
    assert [v.conflict for v in views] == [True]


def test_availability_states_and_mine(env):
    store, _, request, _, _ = env
    a = request.execute(cmd(user_id=1, start_at=at(10), end_at=at(12)))
    store.rows[a.id].approve()
    request.execute(cmd(user_id=2, start_at=at(14), end_at=at(15, 30)))
    request.execute(cmd(user_id=2, room_id=2, start_at=at(9), end_at=at(10)))
    result = GetAvailabilityUseCase(Rooms(), store).execute(date(2026, 10, 13), viewer_id=2)
    by_room = {r.room.id: r for r in result}
    hours = dict(by_room[1].hours)
    assert (hours[9], hours[10], hours[11], hours[12]) == ("free", "approved", "approved", "free")
    assert (hours[14], hours[15], hours[16]) == ("pending", "pending", "free")
    assert set(hours) == set(range(9, 22))
    assert dict(by_room[2].hours)[9] == "pending"
    assert set(dict(by_room[3].hours).values()) == {"blocked"}
    mine = {b.mine for b in by_room[1].blocks}
    assert mine == {True, False}


def test_availability_prefers_approved_over_pending_in_same_hour(env):
    store, _, request, *_ = env
    p = request.execute(cmd(user_id=1, start_at=at(10), end_at=at(11)))
    a = request.execute(cmd(user_id=2, start_at=at(10), end_at=at(11)))
    store.rows[a.id].approve()
    assert p.id != a.id
    result = GetAvailabilityUseCase(Rooms(), store).execute(date(2026, 10, 13), viewer_id=3)
    assert dict(result[0].hours)[10] == "approved"
