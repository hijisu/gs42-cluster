from dataclasses import dataclass
from datetime import datetime, timedelta

from rooms.domain.errors import InvalidRange


@dataclass(frozen=True)
class TimeRange:
    """[start, end) 반개구간. 끝과 시작이 맞닿는 것은 겹침이 아니다."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise InvalidRange("종료 시간은 시작 시간 이후여야 합니다")

    def overlaps(self, other: "TimeRange") -> bool:
        return self.start < other.end and other.start < self.end

    @property
    def duration(self) -> timedelta:
        return self.end - self.start
