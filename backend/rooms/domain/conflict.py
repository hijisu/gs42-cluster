"""시간 충돌 판단 도메인 서비스."""

from collections.abc import Iterable

from rooms.domain.errors import RoomConflict
from rooms.domain.reservation import ReservationStatus, RoomReservation


class ConflictChecker:
    @staticmethod
    def conflicts(
        target: RoomReservation, others: Iterable[RoomReservation]
    ) -> list[RoomReservation]:
        """같은 장소에서 시간이 겹치는 다른 활성(pending/approved) 예약."""
        return [
            o
            for o in others
            if o.id != target.id
            and o.room_id == target.room_id
            and o.is_active
            and o.time_range.overlaps(target.time_range)
        ]

    @staticmethod
    def has_conflict(target: RoomReservation, others: Iterable[RoomReservation]) -> bool:
        return bool(ConflictChecker.conflicts(target, others))

    @staticmethod
    def ensure_can_approve(target: RoomReservation, others: Iterable[RoomReservation]) -> None:
        """이미 승인된 예약과 겹치면 승인할 수 없다(대기끼리 겹침은 허용, 먼저 승인한 쪽이 이김)."""
        approved = [
            o
            for o in ConflictChecker.conflicts(target, others)
            if o.status == ReservationStatus.APPROVED
        ]
        if approved:
            raise RoomConflict("이미 승인된 예약과 시간이 겹칩니다")
