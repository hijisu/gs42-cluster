from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from rooms.domain.reservation import RoomReservation
from rooms.domain.rules import RoomRules


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


@dataclass(frozen=True)
class UserInfo:
    id: int
    intra_id: str
    name: str


@dataclass(frozen=True)
class StaffReservationView:
    view: ReservationView  # conflict 필드는 conflict_ids 존재 여부와 같다
    user: UserInfo
    created_by_staff: bool
    conflict_ids: list[int]


@dataclass(frozen=True)
class StaffReservationRow:
    reservation: RoomReservation
    view: ReservationView
    user: UserInfo


class RoomRepository(Protocol):
    def list_all(self) -> list[RoomInfo]: ...

    def get(self, room_id: int) -> RoomInfo | None: ...

    def create(self, code: str | None, name: str, capacity_note: str, equipment: str) -> RoomInfo:
        """코드가 없으면 자동 생성한다. 코드 중복이면 RoomCodeTaken."""
        ...

    def update(self, room_id: int, changes: dict) -> RoomInfo: ...


class RulesRepository(Protocol):
    def get(self) -> RoomRules: ...

    def save(self, rules: RoomRules) -> None: ...


class ReservationRepository(Protocol):
    def add(self, reservation: RoomReservation) -> RoomReservation: ...

    def get(self, reservation_id: int) -> RoomReservation | None: ...

    def save(self, reservation: RoomReservation) -> None: ...

    def lock_room(self, room_id: int) -> None:
        """같은 장소의 승인 처리를 직렬화한다(트랜잭션 안에서 장소 행 잠금)."""
        ...

    def active_between(self, start: datetime, end: datetime) -> list[RoomReservation]:
        """[start, end) 구간과 겹치는 pending/approved 예약(모든 장소)."""
        ...


class ReservationReadModel(Protocol):
    def get_view(self, reservation_id: int) -> ReservationView: ...

    def list_for_user(self, user_id: int) -> list[ReservationView]: ...

    def list_for_staff(
        self, start: datetime, end: datetime, status: str | None
    ) -> list[StaffReservationRow]:
        """[start, end) 와 겹치는 예약(상태 필터 선택). 시작 시각 순."""
        ...

    def get_for_staff(self, reservation_id: int) -> StaffReservationRow: ...
