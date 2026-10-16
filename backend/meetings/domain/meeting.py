"""면담 신청 집합 루트. 상태 전이 규칙은 모두 여기에 둔다."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from common.domain.errors import ForbiddenError
from meetings.domain.errors import InvalidTransition


class MeetingStatus(StrEnum):
    PENDING = "pending"  # 배정 중
    PROPOSED = "proposed"  # 시간 조율 중
    CONFIRMED = "confirmed"  # 확정
    COMPLETED = "completed"
    CANCELED = "canceled"


_CANCELABLE = {MeetingStatus.PENDING, MeetingStatus.PROPOSED, MeetingStatus.CONFIRMED}


@dataclass
class MeetingRequest:
    student_id: int
    type_id: int
    slot_at: datetime
    content: str
    notify_slack: bool = False
    staff_id: int | None = None
    status: MeetingStatus = MeetingStatus.PENDING
    location: str = ""
    proposed_at: datetime | None = None
    staff_note: str = ""
    id: int | None = None

    def _require(self, allowed: set[MeetingStatus], action: str) -> None:
        if self.status not in allowed:
            raise InvalidTransition(f"{self.status.value} 상태에서는 {action}할 수 없습니다")

    def assign(self, staff_id: int) -> None:
        """담당자를 배정/변경한다. pending/proposed에서만 가능."""
        self._require({MeetingStatus.PENDING, MeetingStatus.PROPOSED}, "assign")
        self.staff_id = staff_id

    def propose(self, staff_id: int, proposed_at: datetime, note: str = "") -> None:
        """다른 시간을 제안한다. pending/proposed → proposed."""
        self._require({MeetingStatus.PENDING, MeetingStatus.PROPOSED}, "propose")
        self.staff_id = staff_id
        self.proposed_at = proposed_at
        self.staff_note = note
        self.status = MeetingStatus.PROPOSED

    def confirm(self, staff_id: int, location: str, note: str = "") -> None:
        """확정한다. pending/proposed → confirmed. 제안된 시간이 있으면 그 시간으로 확정."""
        self._require({MeetingStatus.PENDING, MeetingStatus.PROPOSED}, "confirm")
        if self.proposed_at is not None:
            self.slot_at = self.proposed_at
        self.staff_id = staff_id
        self.location = location
        self.staff_note = note or self.staff_note
        self.status = MeetingStatus.CONFIRMED

    def complete(self) -> None:
        self._require({MeetingStatus.CONFIRMED}, "complete")
        self.status = MeetingStatus.COMPLETED

    def cancel(self, by_student_id: int) -> None:
        """신청한 본인만 취소할 수 있다."""
        if by_student_id != self.student_id:
            raise ForbiddenError("본인의 면담만 취소할 수 있습니다")
        self._require(_CANCELABLE, "cancel")
        self.status = MeetingStatus.CANCELED
