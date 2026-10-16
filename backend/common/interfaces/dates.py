from datetime import date, datetime, time, timedelta

from django.utils import timezone


def day_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    """KST 기준 [start_date 00:00, end_date 24:00) 구간(양끝 포함 비교용으로 마이크로초 차감)."""
    tz = timezone.get_current_timezone()
    start = datetime.combine(start_date, time.min, tzinfo=tz)
    end = datetime.combine(end_date, time.min, tzinfo=tz) + timedelta(days=1)
    return start, end - timedelta(microseconds=1)
