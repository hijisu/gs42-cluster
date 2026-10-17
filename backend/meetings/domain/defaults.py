"""모든 스태프의 기본 면담 가능 시간: 평일 10:00~12:00, 13:00~17:00 (30분 슬롯, KST)."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from meetings.domain.slots import SLOT_MINUTES

KST = ZoneInfo("Asia/Seoul")
# (시작 시각 포함, 종료 시각 제외)
DEFAULT_WINDOWS = ((time(10, 0), time(12, 0)), (time(13, 0), time(17, 0)))
_WEEKEND_FROM = 5  # date.weekday(): 토=5, 일=6


def default_slots(start: datetime, end: datetime) -> list[datetime]:
    """[start, end] 범위(양끝 포함)의 기본 가능 시간 시작 시각 목록(오름차순)."""
    step = timedelta(minutes=SLOT_MINUTES)
    first_day = start.astimezone(KST).date()
    last_day = end.astimezone(KST).date()
    slots: list[datetime] = []
    day = first_day
    while day <= last_day:
        if day.weekday() < _WEEKEND_FROM:
            for open_at, close_at in DEFAULT_WINDOWS:
                current = datetime.combine(day, open_at, tzinfo=KST)
                closing = datetime.combine(day, close_at, tzinfo=KST)
                while current < closing:
                    if start <= current <= end:
                        slots.append(current)
                    current += step
        day += timedelta(days=1)
    return slots
