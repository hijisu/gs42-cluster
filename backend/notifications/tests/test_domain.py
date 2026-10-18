"""도메인 테스트: DB 없이 실행."""

from datetime import UTC, date, datetime, timedelta

from notifications.domain.formatting import fmt_date, fmt_moment, fmt_range
from notifications.domain.notification import Notification, NotificationType

NOW = datetime(2026, 10, 20, 5, 0, tzinfo=UTC)  # 14:00 KST


def make():
    return Notification(user_id=1, type=NotificationType.MEETING_CONFIRMED, title="t")


def test_new_notification_is_unread():
    assert make().is_read is False


def test_mark_read_sets_time_and_is_idempotent():
    n = make()
    n.mark_read(NOW)
    n.mark_read(NOW + timedelta(hours=1))
    assert n.is_read and n.read_at == NOW  # 처음 읽은 시각 유지


def test_formatting_uses_kst():
    assert fmt_moment(NOW) == "10.20 14:00"
    assert fmt_range(NOW, NOW + timedelta(hours=2)) == "10.20 14:00–16:00"
    assert fmt_range(NOW, NOW + timedelta(days=1)) == "10.20 14:00–10.21 14:00"
    assert fmt_date(date(2026, 11, 26)) == "11.26"


def test_late_utc_evening_rolls_over_to_next_kst_day():
    assert fmt_moment(datetime(2026, 10, 20, 16, 30, tzinfo=UTC)) == "10.21 01:30"


def test_type_codes_are_stable_strings():
    assert {t.value for t in NotificationType} == {
        "meeting_confirmed",
        "meeting_proposed",
        "reservation_approved",
        "reservation_rejected",
        "reservation_reassigned",
        "review_requested",
        "meeting_requested",
        "meeting_canceled",
        "reservation_requested",
        "reservation_canceled",
    }
