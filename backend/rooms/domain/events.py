from dataclasses import dataclass
from datetime import datetime

from common.domain.events import DomainEvent


@dataclass(frozen=True)
class ReservationRequested(DomainEvent):
    reservation_id: int
    user_id: int
    room_id: int
    start_at: datetime
    end_at: datetime


@dataclass(frozen=True)
class ReservationCanceled(DomainEvent):
    reservation_id: int
    user_id: int
    room_id: int


@dataclass(frozen=True)
class ReservationApproved(DomainEvent):
    reservation_id: int
    user_id: int
    room_id: int
    start_at: datetime
    end_at: datetime
    room_name: str = ""


@dataclass(frozen=True)
class ReservationRejected(DomainEvent):
    reservation_id: int
    user_id: int
    room_id: int
    reason: str
    room_name: str = ""


@dataclass(frozen=True)
class ReservationReassigned(DomainEvent):
    """대체 장소로 변경하면서 승인했다(승인 알림 + 장소 변경 안내용)."""

    reservation_id: int
    user_id: int
    from_room_id: int
    to_room_id: int
    start_at: datetime
    end_at: datetime
    from_room_name: str = ""
    to_room_name: str = ""
