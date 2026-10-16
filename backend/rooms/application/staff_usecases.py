"""교육운영팀용 유스케이스."""

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta

from common.domain.events import EventDispatcher
from rooms.application.ports import (
    ReservationReadModel,
    ReservationRepository,
    RoomInfo,
    RoomRepository,
    RulesRepository,
    StaffReservationRow,
    StaffReservationView,
)
from rooms.application.usecases import Clock
from rooms.domain.conflict import ConflictChecker
from rooms.domain.errors import ReservationNotFound, RoomBlocked, RoomNotFound
from rooms.domain.events import ReservationApproved, ReservationReassigned, ReservationRejected
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.room import RoomStatus
from rooms.domain.rules import KST, RoomRules
from rooms.domain.time_range import TimeRange


def _load(reservations: ReservationRepository, reservation_id: int) -> RoomReservation:
    reservation = reservations.get(reservation_id)
    if reservation is None:
        raise ReservationNotFound("예약을 찾을 수 없습니다")
    return reservation


def _bookable_room(rooms: RoomRepository, room_id: int) -> RoomInfo:
    room = rooms.get(room_id)
    if room is None:
        raise RoomNotFound("존재하지 않는 장소입니다")
    if room.status == RoomStatus.BLOCKED.value:
        raise RoomBlocked("예약을 받지 않는 장소입니다")
    return room


class _Staff:
    def __init__(
        self,
        rooms: RoomRepository,
        reservations: ReservationRepository,
        read_model: ReservationReadModel,
    ) -> None:
        self._rooms = rooms
        self._reservations = reservations
        self._read = read_model

    def _with_conflicts(self, rows: list[StaffReservationRow]) -> list[StaffReservationView]:
        if not rows:
            return []
        start = min(r.reservation.time_range.start for r in rows)
        end = max(r.reservation.time_range.end for r in rows)
        active = self._reservations.active_between(start, end)
        result = []
        for row in rows:
            ids = (
                [o.id for o in ConflictChecker.conflicts(row.reservation, active)]
                if row.reservation.status == ReservationStatus.PENDING
                else []
            )
            result.append(
                StaffReservationView(
                    view=replace(row.view, conflict=bool(ids)),
                    user=row.user,
                    created_by_staff=row.reservation.created_by_staff,
                    conflict_ids=ids,
                )
            )
        return result

    def _one(self, reservation_id: int) -> StaffReservationView:
        return self._with_conflicts([self._read.get_for_staff(reservation_id)])[0]


class ListStaffReservationsUseCase(_Staff):
    def __init__(self, rooms, reservations, read_model, clock: Clock) -> None:
        super().__init__(rooms, reservations, read_model)
        self._clock = clock

    def execute(self, day: date | None, status: str | None) -> list[StaffReservationView]:
        """date가 있으면 그 날(KST), 없으면 오늘 이후 예약을 돌려준다."""
        if day is not None:
            start = datetime.combine(day, time.min, tzinfo=KST)
            end = start + timedelta(days=1)
        else:
            start = self._clock().astimezone(KST).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=3650)
        return self._with_conflicts(self._read.list_for_staff(start, end, status))


class ApproveReservationUseCase(_Staff):
    def __init__(self, rooms, reservations, read_model, events: EventDispatcher) -> None:
        super().__init__(rooms, reservations, read_model)
        self._events = events

    def _approve(self, reservation: RoomReservation) -> None:
        # 같은 장소의 승인 처리를 직렬화한 뒤 충돌을 검사한다(DB 배타 제약이 최종 방어선).
        self._reservations.lock_room(reservation.room_id)
        others = self._reservations.active_between(
            reservation.time_range.start, reservation.time_range.end
        )
        ConflictChecker.ensure_can_approve(reservation, others)
        reservation.approve()
        self._reservations.save(reservation)

    def execute(self, reservation_id: int) -> StaffReservationView:
        reservation = _load(self._reservations, reservation_id)
        _bookable_room(self._rooms, reservation.room_id)
        self._approve(reservation)
        self._events.publish(
            ReservationApproved(
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                room_id=reservation.room_id,
                start_at=reservation.time_range.start,
                end_at=reservation.time_range.end,
            )
        )
        return self._one(reservation.id)


class RejectReservationUseCase(_Staff):
    def __init__(self, rooms, reservations, read_model, events: EventDispatcher) -> None:
        super().__init__(rooms, reservations, read_model)
        self._events = events

    def execute(self, reservation_id: int, reason: str) -> StaffReservationView:
        reservation = _load(self._reservations, reservation_id)
        reservation.reject(reason)
        self._reservations.save(reservation)
        self._events.publish(
            ReservationRejected(
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                room_id=reservation.room_id,
                reason=reservation.reject_reason,
            )
        )
        return self._one(reservation.id)


class ReassignReservationUseCase(ApproveReservationUseCase):
    """대체 장소로 바꾸고 승인한다."""

    def execute(self, reservation_id: int, room_id: int) -> StaffReservationView:
        reservation = _load(self._reservations, reservation_id)
        _bookable_room(self._rooms, room_id)
        from_room_id = reservation.room_id
        reservation.reassign(room_id)
        self._approve(reservation)
        self._events.publish(
            ReservationReassigned(
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                from_room_id=from_room_id,
                to_room_id=room_id,
                start_at=reservation.time_range.start,
                end_at=reservation.time_range.end,
            )
        )
        return self._one(reservation.id)


@dataclass(frozen=True)
class StaffBookingCommand:
    staff_id: int
    room_id: int
    start_at: datetime
    end_at: datetime
    purpose: str
    headcount: int
    note: str = ""
    user_id: int | None = None  # 대리 예약 대상(없으면 본인)


class StaffBookUseCase(ApproveReservationUseCase):
    """운영팀 직접 예약: 바로 승인 상태로 만든다."""

    def __init__(
        self,
        rooms,
        reservations,
        read_model,
        events,
        clock: Clock,
        rules,  # RulesProvider
    ) -> None:
        super().__init__(rooms, reservations, read_model, events)
        self._clock = clock
        self._rules = rules

    def execute(self, cmd: StaffBookingCommand) -> StaffReservationView:
        _bookable_room(self._rooms, cmd.room_id)
        time_range = TimeRange(cmd.start_at, cmd.end_at)
        self._rules().validate(time_range, now=self._clock())
        target = cmd.user_id or cmd.staff_id
        reservation = self._reservations.add(
            RoomReservation(
                user_id=target,
                room_id=cmd.room_id,
                time_range=time_range,
                purpose=cmd.purpose,
                headcount=cmd.headcount,
                note=cmd.note,
                created_by_staff=True,
            )
        )
        self._approve(reservation)  # 충돌이면 RoomConflict → 호출 측 트랜잭션이 되돌린다
        if target != cmd.staff_id:  # 본인 예약이면 알릴 필요가 없다
            self._events.publish(
                ReservationApproved(
                    reservation_id=reservation.id,
                    user_id=target,
                    room_id=reservation.room_id,
                    start_at=time_range.start,
                    end_at=time_range.end,
                )
            )
        return self._one(reservation.id)


class UpdateRulesUseCase:
    def __init__(self, rules: RulesRepository) -> None:
        self._rules = rules

    def execute(self, open_hour: int, close_hour: int, usage_rules: list[str]) -> RoomRules:
        rules = RoomRules.define(open_hour, close_hour, usage_rules)
        self._rules.save(rules)
        return rules


class CreateRoomUseCase:
    def __init__(self, rooms: RoomRepository) -> None:
        self._rooms = rooms

    def execute(
        self, name: str, code: str | None = None, capacity_note: str = "", equipment: str = ""
    ) -> RoomInfo:
        return self._rooms.create(code, name.strip(), capacity_note, equipment)


class UpdateRoomUseCase:
    """장소 정보 수정과 차단/해제. 차단해도 기존 승인 예약은 유지되고 새 요청만 막힌다."""

    def __init__(self, rooms: RoomRepository) -> None:
        self._rooms = rooms

    def execute(self, room_id: int, changes: dict) -> RoomInfo:
        if self._rooms.get(room_id) is None:
            raise RoomNotFound("존재하지 않는 장소입니다")
        return self._rooms.update(room_id, changes)
