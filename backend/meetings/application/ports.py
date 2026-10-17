from dataclasses import dataclass
from datetime import date, datetime
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


@dataclass(frozen=True)
class StudentInfo:
    id: int
    intra_id: str
    name: str


@dataclass(frozen=True)
class StaffMeetingView:
    """운영팀에게 내려줄 읽기 모델. 교육생 정보와 내부 메모를 포함한다."""

    meeting: MeetingView
    student: StudentInfo
    staff_note: str
    created_at: datetime


@dataclass(frozen=True)
class StaffMeetingTypeView:
    id: int
    code: str
    name: str
    default_staff_id: int | None
    default_staff_name: str | None


class MeetingRepository(Protocol):
    def add(self, meeting: MeetingRequest) -> MeetingRequest: ...

    def get(self, meeting_id: int) -> MeetingRequest | None: ...

    def save(self, meeting: MeetingRequest) -> None: ...

    def confirmed_between(
        self, start: datetime, end: datetime
    ) -> list[tuple[int | None, datetime]]: ...

    def has_confirmed(self, staff_id: int, at: datetime, exclude_id: int | None) -> bool: ...

    def staff_has_confirmed_between(
        self, staff_id: int, start: datetime, end: datetime
    ) -> list[datetime]: ...


class AvailabilityRepository(Protocol):
    def offered_between(self, start: datetime, end: datetime) -> list[tuple[int, datetime]]: ...

    def for_staff_between(
        self, staff_id: int, start: datetime, end: datetime
    ) -> list[datetime]: ...

    def replace_for_staff(
        self, staff_id: int, start: datetime, end: datetime, slots: list[datetime]
    ) -> None: ...

    def customized_days(self, staff_id: int, start: datetime, end: datetime) -> list[date]:
        """범위 안에서 직접 저장해 기본 가능 시간을 쓰지 않는 날(KST)."""
        ...

    def reset_to_default(self, staff_id: int, start: datetime, end: datetime) -> None: ...


class MeetingTypeRepository(Protocol):
    def list_all(self) -> list[MeetingTypeInfo]: ...

    def get(self, type_id: int) -> MeetingTypeInfo | None: ...

    def set_default_staff(self, type_id: int, staff_id: int | None) -> None: ...


class MeetingReadModel(Protocol):
    def get_view(self, meeting_id: int) -> MeetingView: ...

    def list_for_student(self, student_id: int) -> list[MeetingView]: ...


class StaffDirectory(Protocol):
    def is_staff(self, user_id: int) -> bool: ...


class StaffMeetingReadModel(Protocol):
    def get(self, meeting_id: int) -> StaffMeetingView: ...

    def list_meetings(self, status: str | None) -> list[StaffMeetingView]: ...

    def list_types(self) -> list[StaffMeetingTypeView]: ...
