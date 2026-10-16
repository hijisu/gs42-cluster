"""알림 문구용 시각 표기(KST)."""

from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def fmt_moment(moment: datetime) -> str:
    return moment.astimezone(KST).strftime("%m.%d %H:%M")


def fmt_range(start: datetime, end: datetime) -> str:
    s, e = start.astimezone(KST), end.astimezone(KST)
    if s.date() == e.date():
        return f"{s:%m.%d %H:%M}–{e:%H:%M}"
    return f"{s:%m.%d %H:%M}–{e:%m.%d %H:%M}"


def fmt_date(day) -> str:
    return f"{day:%m.%d}"
