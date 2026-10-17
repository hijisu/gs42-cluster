"""면담 가능 시간을 보고 바꿀 수 있는 날짜 범위: 오늘(KST)부터 4주(이번 주 포함, 월~일 기준)."""

from datetime import date, timedelta

from meetings.domain.errors import AvailabilityBeyondWindow, AvailabilityInPast

WEEKS = 4


def week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def last_day(today: date) -> date:
    """4주째의 일요일. 오늘이 어느 요일이든 이번 주를 1주로 센다."""
    return week_start(today) + timedelta(weeks=WEEKS) - timedelta(days=1)


def ensure_editable(first: date, last: date, today: date) -> None:
    """저장·초기화: 오늘 ~ 4주째 일요일. 지난 날짜는 바꿀 수 없다."""
    if first < today:
        raise AvailabilityInPast("지난 날짜의 가능 시간은 바꿀 수 없습니다")
    if last > last_day(today):
        raise AvailabilityBeyondWindow(
            "가능 시간은 오늘부터 4주(이번 주 포함) 안에서만 설정할 수 있습니다"
        )


def ensure_readable(first: date, last: date, today: date) -> None:
    """조회: 주 단위 화면이 열리도록 이번 주 월요일 ~ 4주째 일요일."""
    if first < week_start(today):
        raise AvailabilityInPast("이번 주 이전의 가능 시간은 조회할 수 없습니다")
    if last > last_day(today):
        raise AvailabilityBeyondWindow(
            "가능 시간은 오늘부터 4주(이번 주 포함) 안에서만 조회할 수 있습니다"
        )
