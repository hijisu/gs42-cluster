"""회의실 예약 집합 루트. 상태 전이 규칙은 모두 여기에 둔다."""

from dataclasses import dataclass
from enum import StrEnum

from common.domain.errors import ForbiddenError
from rooms.domain.errors import InvalidTransition, NotCancelable, ReasonRequired
from rooms.domain.time_range import TimeRange


class ReservationStatus(StrEnum):
    PENDING = "pending"  # 승인 대기
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"


ACTIVE = frozenset({ReservationStatus.PENDING, ReservationStatus.APPROVED})


@dataclass
class RoomReservation:
    user_id: int
    room_id: int
    time_range: TimeRange
    purpose: str
    headcount: int
    note: str = ""
    requested_room_id: int | None = None  # 처음 요청한 장소(재배정되어도 유지)
    status: ReservationStatus = ReservationStatus.PENDING
    reject_reason: str = ""
    created_by_staff: bool = False
    id: int | None = None

    def __post_init__(self) -> None:
        if self.requested_room_id is None:
            self.requested_room_id = self.room_id

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE

    def _require(self, allowed: set[ReservationStatus], action: str) -> None:
        if self.status not in allowed:
            raise InvalidTransition(f"{self.status.value} 상태에서는 {action}할 수 없습니다")

    def approve(self) -> None:
        """pending → approved. 충돌 여부는 ConflictChecker로 호출 측에서 먼저 확인한다."""
        self._require({ReservationStatus.PENDING}, "approve")
        self.status = ReservationStatus.APPROVED

    def reject(self, reason: str) -> None:
        """pending → rejected. 사유는 필수(교육생에게 그대로 보여 준다)."""
        self._require({ReservationStatus.PENDING}, "reject")
        if not reason.strip():
            raise ReasonRequired("반려 사유를 입력해 주세요")
        self.status = ReservationStatus.REJECTED
        self.reject_reason = reason.strip()

    def reassign(self, room_id: int) -> None:
        """다른 장소로 대체 배정한다. pending/approved에서 가능."""
        self._require(set(ACTIVE), "reassign")
        self.room_id = room_id

    def cancel(self, by_user_id: int) -> None:
        """신청한 본인만, 승인 전(pending)에만 취소할 수 있다. 승인된 예약은 운영팀이 취소한다."""
        if by_user_id != self.user_id:
            raise ForbiddenError("본인의 예약만 취소할 수 있습니다")
        if self.status != ReservationStatus.PENDING:
            raise NotCancelable("승인된 예약은 직접 취소할 수 없습니다. 운영팀에 문의해 주세요")
        self.status = ReservationStatus.CANCELED

    def cancel_by_staff(self) -> None:
        """운영팀 취소: 승인된 예약도 취소할 수 있다(pending/approved)."""
        self._require(set(ACTIVE), "cancel")
        self.status = ReservationStatus.CANCELED
