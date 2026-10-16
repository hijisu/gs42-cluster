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
