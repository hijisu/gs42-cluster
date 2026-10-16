"""슬롯 가용성 계산: 담당자 가능 슬롯 − 확정된 면담."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

SLOT_MINUTES = 30


@dataclass(frozen=True)
class SlotAvailability:
    start_at: datetime
    remaining: int

    @property
    def available(self) -> bool:
        return self.remaining > 0


def is_aligned(start_at: datetime) -> bool:
    """30분 단위(정각/30분, 초 없음)인지."""
    return (
        start_at.minute % SLOT_MINUTES == 0 and start_at.second == 0 and start_at.microsecond == 0
    )


def compute_slots(
    offered: Iterable[tuple[int, datetime]],
    confirmed: Iterable[tuple[int | None, datetime]],
    now: datetime,
) -> list[SlotAvailability]:
    """시간대별 남은 담당자 수를 계산한다. 지난 시간은 남은 수 0.

    offered: (staff_id, start_at) 담당자가 연 슬롯.
    confirmed: (staff_id, slot_at) 확정된 면담. 담당자 없는 확정 건은 해당 시각 1자리를 차지한다.
    """
    staff_by_time: dict[datetime, set[int]] = defaultdict(set)
    for staff_id, start_at in offered:
        staff_by_time[start_at].add(staff_id)

    busy_staff: dict[datetime, set[int]] = defaultdict(set)
    unassigned: dict[datetime, int] = defaultdict(int)
    for staff_id, slot_at in confirmed:
        if staff_id is None:
            unassigned[slot_at] += 1
        else:
            busy_staff[slot_at].add(staff_id)

    result = []
    for start_at in sorted(staff_by_time):
        free = len(staff_by_time[start_at] - busy_staff[start_at]) - unassigned[start_at]
        remaining = max(free, 0) if start_at > now else 0
        result.append(SlotAvailability(start_at=start_at, remaining=remaining))
    return result
