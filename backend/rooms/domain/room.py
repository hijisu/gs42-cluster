from enum import StrEnum


class RoomStatus(StrEnum):
    OPEN = "open"  # 예약받음
    BLOCKED = "blocked"  # 차단
