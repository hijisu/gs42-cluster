from dataclasses import dataclass
from datetime import datetime

from common.domain.events import DomainEvent


@dataclass(frozen=True)
class MeetingRequested(DomainEvent):
    meeting_id: int
    student_id: int
    type_id: int
    slot_at: datetime
    staff_id: int | None


@dataclass(frozen=True)
class MeetingCanceled(DomainEvent):
    meeting_id: int
    student_id: int
    staff_id: int | None
