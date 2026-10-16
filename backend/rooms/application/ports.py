from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from rooms.domain.reservation import RoomReservation


@dataclass(frozen=True)
class RoomInfo:
    id: int
    code: str
    name: str
    capacity_note: str
    equipment: str
    status: str


@dataclass(frozen=True)
class ReservationView:
    id: int
    room: RoomInfo
    requested_room: RoomInfo
    start_at: datetime
    end_at: datetime
    purpose: str
    headcount: int
    note: str
    status: str
    reject_reason: str
    conflict: bool = False


class RoomRepository(Protocol):
    def list_all(self) -> list[RoomInfo]: ...

    def get(self, room_id: int) -> RoomInfo | None: ...


class ReservationRepository(Protocol):
    def add(self, reservation: RoomReservation) -> RoomReservation: ...

    def get(self, reservation_id: int) -> RoomReservation | None: ...

    def save(self, reservation: RoomReservation) -> None: ...

    def active_between(self, start: datetime, end: datetime) -> list[RoomReservation]:
        """[start, end) 구간과 겹치는 pending/approved 예약(모든 장소)."""
        ...


class ReservationReadModel(Protocol):
    def get_view(self, reservation_id: int) -> ReservationView: ...

    def list_for_user(self, user_id: int) -> list[ReservationView]: ...
