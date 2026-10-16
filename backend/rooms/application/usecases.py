from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from common.domain.events import EventDispatcher
from rooms.application.ports import (
    ReservationReadModel,
    ReservationRepository,
    ReservationView,
    RoomInfo,
    RoomRepository,
)
from rooms.domain.conflict import ConflictChecker
from rooms.domain.errors import ReservationNotFound, RoomBlocked, RoomNotFound
from rooms.domain.events import ReservationCanceled, ReservationRequested
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.room import RoomStatus
from rooms.domain.rules import DEFAULT_RULES, KST, RoomRules
from rooms.domain.time_range import TimeRange

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class RequestReservationCommand:
    user_id: int
    room_id: int
    start_at: datetime
    end_at: datetime
    purpose: str
    headcount: int
    note: str = ""


@dataclass(frozen=True)
class AvailabilityBlock:
    reservation_id: int
    start_at: datetime
    end_at: datetime
    status: str
    purpose: str
    headcount: int
    mine: bool


@dataclass(frozen=True)
class RoomAvailability:
    room: RoomInfo
    blocks: list[AvailabilityBlock]
    hours: list[tuple[int, str]]  # (시, "approved" | "pending" | "free" | "blocked")


def _with_conflict(view: ReservationView, reservation: RoomReservation, others) -> ReservationView:
    pending = reservation.status == ReservationStatus.PENDING
    return replace(view, conflict=pending and ConflictChecker.has_conflict(reservation, others))


class ListRoomsUseCase:
    def __init__(self, rooms: RoomRepository) -> None:
        self._rooms = rooms

    def execute(self) -> list[RoomInfo]:
        return self._rooms.list_all()


class GetRulesUseCase:
    def __init__(self, rules: RoomRules = DEFAULT_RULES) -> None:
        self._rules = rules

    def execute(self) -> RoomRules:
        return self._rules


class GetAvailabilityUseCase:
    def __init__(
        self,
        rooms: RoomRepository,
        reservations: ReservationRepository,
        rules: RoomRules = DEFAULT_RULES,
    ) -> None:
        self._rooms = rooms
        self._reservations = reservations
        self._rules = rules

    def execute(self, day: date, viewer_id: int) -> list[RoomAvailability]:
        start = datetime.combine(day, time(self._rules.open_hour), tzinfo=KST)
        end = datetime.combine(day, time(self._rules.close_hour), tzinfo=KST)
        day_reservations = self._reservations.active_between(start, end)
        result = []
        for room in self._rooms.list_all():
            mine = [r for r in day_reservations if r.room_id == room.id]
            blocks = [
                AvailabilityBlock(
                    reservation_id=r.id,
                    start_at=r.time_range.start,
                    end_at=r.time_range.end,
                    status=r.status.value,
                    purpose=r.purpose,
                    headcount=r.headcount,
                    mine=r.user_id == viewer_id,
                )
                for r in sorted(mine, key=lambda r: r.time_range.start)
            ]
            hours = []
            for hour in range(self._rules.open_hour, self._rules.close_hour):
                cell = TimeRange(
                    datetime.combine(day, time(hour), tzinfo=KST),
                    datetime.combine(day, time(hour), tzinfo=KST) + timedelta(hours=1),
                )
                states = {r.status for r in mine if r.time_range.overlaps(cell)}
                if room.status == RoomStatus.BLOCKED.value:
                    state = "blocked"
                elif ReservationStatus.APPROVED in states:
                    state = "approved"
                elif ReservationStatus.PENDING in states:
                    state = "pending"
                else:
                    state = "free"
                hours.append((hour, state))
            result.append(RoomAvailability(room=room, blocks=blocks, hours=hours))
        return result


class RequestReservationUseCase:
    def __init__(
        self,
        rooms: RoomRepository,
        reservations: ReservationRepository,
        read_model: ReservationReadModel,
        events: EventDispatcher,
        clock: Clock,
        rules: RoomRules = DEFAULT_RULES,
    ) -> None:
        self._rooms = rooms
        self._reservations = reservations
        self._read = read_model
        self._events = events
        self._clock = clock
        self._rules = rules

    def execute(self, cmd: RequestReservationCommand) -> ReservationView:
        room = self._rooms.get(cmd.room_id)
        if room is None:
            raise RoomNotFound("존재하지 않는 장소입니다")
        if room.status == RoomStatus.BLOCKED.value:
            raise RoomBlocked("예약을 받지 않는 장소입니다")
        time_range = TimeRange(cmd.start_at, cmd.end_at)
        self._rules.validate(time_range, now=self._clock())

        reservation = self._reservations.add(
            RoomReservation(
                user_id=cmd.user_id,
                room_id=room.id,
                time_range=time_range,
                purpose=cmd.purpose,
                headcount=cmd.headcount,
                note=cmd.note,
            )
        )
        # 대기 요청은 겹쳐도 접수하고, 충돌 여부만 플래그로 알려 준다.
        others = self._reservations.active_between(time_range.start, time_range.end)
        self._events.publish(
            ReservationRequested(
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                room_id=reservation.room_id,
                start_at=time_range.start,
                end_at=time_range.end,
            )
        )
        return _with_conflict(self._read.get_view(reservation.id), reservation, others)


class CancelReservationUseCase:
    def __init__(
        self,
        reservations: ReservationRepository,
        read_model: ReservationReadModel,
        events: EventDispatcher,
    ) -> None:
        self._reservations = reservations
        self._read = read_model
        self._events = events

    def execute(self, reservation_id: int, user_id: int) -> ReservationView:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ReservationNotFound("예약을 찾을 수 없습니다")
        reservation.cancel(by_user_id=user_id)
        self._reservations.save(reservation)
        self._events.publish(
            ReservationCanceled(
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                room_id=reservation.room_id,
            )
        )
        return self._read.get_view(reservation.id)


class ListMyReservationsUseCase:
    def __init__(
        self, reservations: ReservationRepository, read_model: ReservationReadModel
    ) -> None:
        self._reservations = reservations
        self._read = read_model

    def execute(self, user_id: int) -> list[ReservationView]:
        views = self._read.list_for_user(user_id)
        pending = [v for v in views if v.status == ReservationStatus.PENDING.value]
        if not pending:
            return views
        start = min(v.start_at for v in pending)
        end = max(v.end_at for v in pending)
        others = self._reservations.active_between(start, end)
        by_id = {r.id: r for r in others}
        return [
            _with_conflict(v, by_id[v.id], others)
            if v.status == ReservationStatus.PENDING.value and v.id in by_id
            else v
            for v in views
        ]
