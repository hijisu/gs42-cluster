from datetime import date, datetime

import pytest

from rooms.domain.block import BlockPolicy, Repeat, RoomBlock
from rooms.domain.errors import InvalidBlock, RoomBlockedPeriod
from rooms.domain.rules import KST
from rooms.domain.time_range import TimeRange


def tr(day: str, start: str, end: str) -> TimeRange:
    y, m, d = map(int, day.split("-"))
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return TimeRange(datetime(y, m, d, sh, sm, tzinfo=KST), datetime(y, m, d, eh, em, tzinfo=KST))


SAT = "2030-01-12"  # 토요일


def test_single_block_has_one_occurrence():
    block = RoomBlock(room_id=1, time_range=tr(SAT, "10:00", "12:00"), reason="수학 교육")
    [only] = block.occurrences()
    assert only.day == date(2030, 1, 12) and only.time_range == tr(SAT, "10:00", "12:00")


def test_weekly_saturday_for_a_month():
    block = RoomBlock(
        room_id=1,
        time_range=tr(SAT, "10:00", "12:00"),
        reason="수학 교육",
        repeat=Repeat.WEEKLY,
        weekdays=frozenset({5}),
        until=date(2030, 2, 9),
    )
    days = [o.day for o in block.occurrences()]
    assert days == [
        date(2030, 1, 12),
        date(2030, 1, 19),
        date(2030, 1, 26),
        date(2030, 2, 2),
        date(2030, 2, 9),
    ]
    assert all(
        o.time_range.start.hour == 10 and o.time_range.end.hour == 12 for o in block.occurrences()
    )


def test_weekdays_repeat_skips_weekends():
    block = RoomBlock(
        room_id=1,
        time_range=tr("2030-01-07", "18:00", "21:00"),  # 월
        reason="영어 교육",
        repeat=Repeat.WEEKDAYS,
        until=date(2030, 1, 14),
    )
    assert [o.day.isoformat() for o in block.occurrences()] == [
        "2030-01-07", "2030-01-08", "2030-01-09", "2030-01-10", "2030-01-11", "2030-01-14",
    ]  # fmt: skip


def test_daily_repeat_and_window_filter():
    block = RoomBlock(
        room_id=1,
        time_range=tr("2030-01-07", "09:00", "10:00"),
        reason="점검",
        repeat=Repeat.DAILY,
        until=date(2030, 1, 20),
    )
    window = tr("2030-01-10", "00:00", "23:59")
    assert [o.day.day for o in block.occurrences(window)] == [10]
    assert len(block.occurrences()) == 14


def test_skip_one_occurrence():
    block = RoomBlock(
        room_id=1,
        time_range=tr(SAT, "10:00", "12:00"),
        reason="수학",
        repeat=Repeat.WEEKLY,
        weekdays=frozenset({5}),
        until=date(2030, 1, 26),
    )
    block.skip(date(2030, 1, 19))
    assert [o.day.day for o in block.occurrences()] == [12, 26]
    with pytest.raises(InvalidBlock):
        block.skip(date(2030, 1, 20))  # 토요일이 아니라 회차가 없음


def test_validation():
    base = dict(room_id=1, time_range=tr(SAT, "10:00", "12:00"), reason="x")
    with pytest.raises(InvalidBlock):
        RoomBlock(**{**base, "reason": "  "})
    with pytest.raises(InvalidBlock):  # 반복인데 종료일 없음
        RoomBlock(**base, repeat=Repeat.DAILY)
    with pytest.raises(InvalidBlock):  # 종료일이 첫 회차 이전
        RoomBlock(**base, repeat=Repeat.DAILY, until=date(2030, 1, 1))
    with pytest.raises(InvalidBlock):  # 1년 초과
        RoomBlock(**base, repeat=Repeat.DAILY, until=date(2031, 6, 1))
    with pytest.raises(InvalidBlock):  # 매주인데 요일 없음
        RoomBlock(**base, repeat=Repeat.WEEKLY, until=date(2030, 2, 1))
    with pytest.raises(InvalidBlock):  # 24시간 초과
        RoomBlock(
            room_id=1,
            time_range=TimeRange(
                datetime(2030, 1, 7, 9, tzinfo=KST), datetime(2030, 1, 8, 10, tzinfo=KST)
            ),
            reason="x",
        )


def test_none_repeat_ignores_until_and_weekdays():
    block = RoomBlock(
        room_id=1,
        time_range=tr(SAT, "10:00", "12:00"),
        reason="x",
        weekdays=frozenset({1}),
        until=date(2030, 3, 1),
    )
    assert block.until is None and block.weekdays == frozenset()


def test_policy_blocks_overlap_only_in_same_room_and_not_when_touching():
    block = RoomBlock(room_id=1, time_range=tr(SAT, "10:00", "12:00"), reason="수학")
    with pytest.raises(RoomBlockedPeriod):
        BlockPolicy.ensure_free([block], 1, tr(SAT, "11:00", "13:00"))
    BlockPolicy.ensure_free([block], 2, tr(SAT, "11:00", "13:00"))  # 다른 장소
    BlockPolicy.ensure_free([block], 1, tr(SAT, "12:00", "13:00"))  # 맞닿음은 겹침 아님
    BlockPolicy.ensure_free([block], 1, tr(SAT, "08:00", "10:00"))


def test_changed_revalidates_and_keeps_skipped():
    block = RoomBlock(
        room_id=1, time_range=tr(SAT, "10:00", "12:00"), reason="수학",
        repeat=Repeat.WEEKLY, weekdays=frozenset({5}), until=date(2030, 2, 2),
    )  # fmt: skip
    block.skip(date(2030, 1, 19))
    moved = block.changed(time_range=tr(SAT, "13:00", "15:00"))
    assert date(2030, 1, 19) in moved.skipped and moved.occurrences()[0].time_range.start.hour == 13
    with pytest.raises(InvalidBlock):
        block.changed(reason=" ")
