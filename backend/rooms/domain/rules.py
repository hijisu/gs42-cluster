"""회의실 이용 규칙(RoomRules). 운영시간·시간 단위·과거 시간 검사와 이용수칙 문구."""

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from rooms.domain.errors import InvalidRange, OutsideHours, PastTime
from rooms.domain.time_range import TimeRange

KST = ZoneInfo("Asia/Seoul")

USAGE_RULES = (
    "음료만 반입 가능하며 음식 섭취는 불가합니다.",
    "TV 사용 후 전원 끄기",
    "책상 및 기자재 사용 후 원위치",
    "사용한 냉난방기 전원 끄기",
    "쓰레기 치우기",
    "예약 시간 준수",
)


@dataclass(frozen=True)
class RoomRules:
    open_hour: int = 9
    close_hour: int = 22
    step_minutes: int = 30
    usage_rules: tuple[str, ...] = USAGE_RULES

    def validate(self, requested: TimeRange, now: datetime) -> None:
        """과거 시간, 30분 단위가 아님, 운영시간(09~22시, 하루 안) 밖이면 거부한다."""
        if requested.start < now:
            raise PastTime("과거 시간은 예약할 수 없습니다")
        start, end = requested.start.astimezone(KST), requested.end.astimezone(KST)
        for moment in (start, end):
            if moment.minute % self.step_minutes or moment.second or moment.microsecond:
                raise InvalidRange(f"예약 시간은 {self.step_minutes}분 단위여야 합니다")
        opens = datetime.combine(start.date(), time(self.open_hour), tzinfo=KST)
        closes = datetime.combine(start.date(), time(self.close_hour), tzinfo=KST)
        if start < opens or end > closes:
            raise OutsideHours(
                f"운영시간({self.open_hour}~{self.close_hour}시) 안에서만 예약할 수 있습니다"
            )


DEFAULT_RULES = RoomRules()
