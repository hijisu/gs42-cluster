"""회의실 예약 차단 기간(반복 일정 지원). 캘린더 이벤트처럼 한 번 또는 반복으로 시간을 막는다."""

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from enum import StrEnum

from rooms.domain.errors import InvalidBlock, RoomBlockedPeriod
from rooms.domain.rules import KST
from rooms.domain.time_range import TimeRange

MAX_SPAN_DAYS = 366  # 반복 종료일은 첫 회차에서 최대 1년
MAX_DURATION = timedelta(hours=24)
WEEKDAYS_MON_FRI = frozenset({0, 1, 2, 3, 4})


class Repeat(StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"  # weekdays 로 요일 지정(0=월 … 6=일)
    WEEKDAYS = "weekdays"  # 평일(월~금)


@dataclass(frozen=True)
class Occurrence:
    day: date  # 회차의 KST 날짜(건너뛰기·한 회차 수정의 키)
    time_range: TimeRange


@dataclass
class RoomBlock:
    """room_id 의 `time_range`(첫 회차)를 repeat 규칙대로 until(포함)까지 되풀이해 막는다."""

    room_id: int
    time_range: TimeRange
    reason: str
    repeat: Repeat = Repeat.NONE
    weekdays: frozenset[int] = frozenset()
    until: date | None = None
    skipped: set[date] = field(default_factory=set)
    id: int | None = None

    def __post_init__(self) -> None:
        self.reason = self.reason.strip()
        if not self.reason:
            raise InvalidBlock("차단 사유를 입력해 주세요")
        if self.time_range.duration > MAX_DURATION:
            raise InvalidBlock("한 회차는 24시간을 넘을 수 없습니다")
        first = self.first_day
        if self.repeat == Repeat.NONE:
            self.weekdays, self.until = frozenset(), None
            return
        if self.until is None:
            raise InvalidBlock("반복하려면 반복 종료일이 필요합니다")
        if self.until < first:
            raise InvalidBlock("반복 종료일은 첫 회차 날짜 이후여야 합니다")
        if (self.until - first).days > MAX_SPAN_DAYS:
            raise InvalidBlock("반복은 첫 회차부터 최대 1년까지 설정할 수 있습니다")
        if self.repeat == Repeat.WEEKLY:
            if not self.weekdays or not all(0 <= d <= 6 for d in self.weekdays):
                raise InvalidBlock("매주 반복에는 요일(0=월 ~ 6=일)을 하나 이상 지정해야 합니다")
            self.weekdays = frozenset(self.weekdays)
        else:
            self.weekdays = frozenset()

    @property
    def first_day(self) -> date:
        return self.time_range.start.astimezone(KST).date()

    def _matches(self, day: date) -> bool:
        if self.repeat == Repeat.NONE:
            return day == self.first_day
        if self.until is None or day < self.first_day or day > self.until:
            return False
        if self.repeat == Repeat.DAILY:
            return True
        if self.repeat == Repeat.WEEKDAYS:
            return day.weekday() in WEEKDAYS_MON_FRI
        return day.weekday() in self.weekdays

    def _occurrence_on(self, day: date) -> TimeRange:
        local_start = self.time_range.start.astimezone(KST)
        local_end = self.time_range.end.astimezone(KST)
        # 벽시계 시각(KST)을 유지한 채 날짜만 옮긴다.
        start = datetime.combine(day, local_start.timetz().replace(tzinfo=None), tzinfo=KST)
        end = start + (local_end - local_start)
        return TimeRange(start, end)

    def occurrences(self, window: TimeRange | None = None) -> list[Occurrence]:
        """window 와 겹치는 회차(건너뛴 회차 제외). window 가 없으면 전체."""
        last = self.until if self.repeat != Repeat.NONE else self.first_day
        assert last is not None
        found, day = [], self.first_day
        while day <= last:
            if self._matches(day) and day not in self.skipped:
                tr = self._occurrence_on(day)
                if window is None or tr.overlaps(window):
                    found.append(Occurrence(day, tr))
            day += timedelta(days=1)
        return found

    def conflicts_with(self, other: TimeRange) -> bool:
        return bool(self.occurrences(other))

    def skip(self, day: date) -> None:
        if not any(o.day == day for o in self.occurrences()):
            raise InvalidBlock("해당 날짜에는 이 차단 회차가 없습니다")
        self.skipped.add(day)

    def occurrence_range(self, day: date) -> TimeRange:
        if not any(o.day == day for o in self.occurrences()):
            raise InvalidBlock("해당 날짜에는 이 차단 회차가 없습니다")
        return self._occurrence_on(day)

    def has_occurrences(self) -> bool:
        return bool(self.occurrences())

    def changed(self, **changes) -> "RoomBlock":
        """검증을 다시 거친 새 객체(시리즈 수정용). 건너뛴 회차는 유지한다."""
        return replace(self, **changes)


class BlockPolicy:
    """차단 시간과 겹치는 예약은 불가."""

    @staticmethod
    def ensure_free(blocks: Iterable[RoomBlock], room_id: int, requested: TimeRange) -> None:
        for block in blocks:
            if block.room_id == room_id and block.conflicts_with(requested):
                raise RoomBlockedPeriod("차단된 시간입니다: " + block.reason)
