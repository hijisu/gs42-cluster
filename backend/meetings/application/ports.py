from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from meetings.domain.meeting import MeetingRequest


@dataclass(frozen=True)
class MeetingTypeInfo:
    id: int
    code: str
    name: str
    default_staff_id: int | None


@dataclass(frozen=True)
class MeetingView:
    """교육생에게 내려줄 읽기 모델. status는 코드값."""

    id: int
    type: MeetingTypeInfo
    slot_at: datetime
    content: str
    notify_slack: bool
    status: str
    staff_id: int | None
    staff_name: str | None
    location: str
    proposed_at: datetime | None


class MeetingRepository(Protocol):
    def add(self, meeting: MeetingRequest) -> MeetingRequest: ...

    def get(self, meeting_id: int) -> MeetingRequest | None: ...

    def save(self, meeting: MeetingRequest) -> None: ...

    def confirmed_between(
        self, start: datetime, end: datetime
    ) -> list[tuple[int | None, datetime]]: ...


class AvailabilityRepository(Protocol):
    def offered_between(self, start: datetime, end: datetime) -> list[tuple[int, datetime]]: ...


class MeetingTypeRepository(Protocol):
    def list_all(self) -> list[MeetingTypeInfo]: ...

    def get(self, type_id: int) -> MeetingTypeInfo | None: ...


class MeetingReadModel(Protocol):
    def get_view(self, meeting_id: int) -> MeetingView: ...

    def list_for_student(self, student_id: int) -> list[MeetingView]: ...
