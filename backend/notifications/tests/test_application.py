"""유스케이스 테스트: DB 없이 가짜 채널·사용자 디렉터리 사용."""

from datetime import UTC, date, datetime, timedelta

import pytest

from common.infrastructure.dispatcher import InProcessEventDispatcher
from meetings.domain.events import MeetingConfirmed, MeetingProposed
from notifications.application.handlers import NotificationHandlers, register_handlers
from notifications.application.service import NotificationService
from notifications.domain.notification import NotificationType
from reviews.domain.events import ReviewRequested
from rooms.domain.events import ReservationApproved, ReservationReassigned, ReservationRejected

START = datetime(2026, 10, 20, 5, 0, tzinfo=UTC)  # 14:00 KST
END = START + timedelta(hours=2)


class Channel:
    def __init__(self, name="fake", fail=False):
        self.name, self.fail, self.sent = name, fail, []

    def send(self, notification):
        if self.fail:
            raise RuntimeError("boom")
        self.sent.append(notification)


class Users:
    def __init__(self, mapping):
        self.mapping = mapping

    def ids_by_intra_ids(self, intra_ids):
        return {i: self.mapping[i] for i in intra_ids if i in self.mapping}


def build(channel=None, users=None):
    channel = channel or Channel()
    handlers = NotificationHandlers(NotificationService([channel]), users or Users({}))
    return channel, handlers


# ── 서비스: 채널 분리 ──
def test_one_failing_channel_does_not_block_others_and_is_reported(caplog):
    bad, good = Channel("push", fail=True), Channel("in_app")
    failed = NotificationService([bad, good]).notify(1, NotificationType.MEETING_CONFIRMED, "t")
    assert failed == ["push"] and len(good.sent) == 1
    assert "알림 채널 전송 실패" in caplog.text


def test_failing_first_channel_still_delivers_to_later_ones():
    first, second = Channel("in_app", fail=True), Channel("push")
    NotificationService([first, second]).notify(1, NotificationType.MEETING_CONFIRMED, "t")
    assert len(second.sent) == 1


def test_all_channels_receive_same_notification_content():
    a, b = Channel("a"), Channel("b")
    NotificationService([a, b]).notify(
        7, NotificationType.RESERVATION_APPROVED, "제목", "본문", "/room", {"k": 1}
    )
    for ch in (a, b):
        (n,) = ch.sent
        assert (n.user_id, n.title, n.body, n.link, n.data) == (
            7,
            "제목",
            "본문",
            "/room",
            {"k": 1},
        )


# ── 이벤트 → 알림 ──
def test_meeting_confirmed_notifies_the_student_with_time_and_place():
    channel, h = build()
    h.on_meeting_confirmed(
        MeetingConfirmed(
            meeting_id=3, student_id=11, staff_id=2, slot_at=START, location="1층 사무실 앞"
        )
    )
    (n,) = channel.sent
    assert (n.user_id, n.type, n.link) == (11, NotificationType.MEETING_CONFIRMED, "/meeting")
    assert n.body == "10.20 14:00 · 1층 사무실 앞" and n.data["meeting_id"] == 3


def test_meeting_proposed_notifies_the_student():
    channel, h = build()
    h.on_meeting_proposed(
        MeetingProposed(meeting_id=3, student_id=11, staff_id=2, proposed_at=START)
    )
    (n,) = channel.sent
    assert n.type == NotificationType.MEETING_PROPOSED and "10.20 14:00" in n.body


def test_reservation_approved_mentions_room_and_range():
    channel, h = build()
    h.on_reservation_approved(
        ReservationApproved(
            reservation_id=5,
            user_id=12,
            room_id=1,
            start_at=START,
            end_at=END,
            room_name="다목적회의실",
        )
    )
    (n,) = channel.sent
    assert n.user_id == 12 and n.body == "다목적회의실 · 10.20 14:00–16:00" and n.link == "/room"


def test_reservation_rejected_includes_reason():
    channel, h = build()
    h.on_reservation_rejected(
        ReservationRejected(
            reservation_id=5, user_id=12, room_id=1, reason="기존 예약", room_name="다목적회의실"
        )
    )
    (n,) = channel.sent
    assert n.type == NotificationType.RESERVATION_REJECTED and n.body == "다목적회의실 · 기존 예약"
    assert n.data["reason"] == "기존 예약"


def test_reservation_reassigned_mentions_both_rooms():
    channel, h = build()
    h.on_reservation_reassigned(
        ReservationReassigned(
            reservation_id=5,
            user_id=12,
            from_room_id=1,
            to_room_id=2,
            start_at=START,
            end_at=END,
            from_room_name="다목적회의실",
            to_room_name="유니버스룸(소)",
        )
    )
    (n,) = channel.sent
    assert n.body.startswith("다목적회의실 → 유니버스룸(소)") and n.data["to_room_id"] == 2


def test_review_requested_goes_to_registered_users_only_and_skips_unknown():
    channel, h = build(users=Users({"alice": 1, "bob": 2}))
    h.on_review_requested(
        ReviewRequested(
            course_id=4,
            course_name="파이썬 AI 교육",
            intra_ids=("alice", "bob", "newbie"),
            review_deadline=date(2026, 11, 26),
            message="",
        )
    )
    assert [n.user_id for n in channel.sent] == [1, 2]
    n = channel.sent[0]
    assert n.title == "파이썬 AI 교육 후기를 남겨 주세요" and n.body.endswith("(마감 11.26)")
    assert n.link == "/reviews" and n.data == {"course_id": 4, "review_deadline": "2026-11-26"}


def test_review_requested_uses_custom_message_and_handles_no_deadline():
    channel, h = build(users=Users({"alice": 1}))
    h.on_review_requested(
        ReviewRequested(
            course_id=4,
            course_name="c",
            intra_ids=("alice",),
            review_deadline=None,
            message="꼭 써 주세요",
        )
    )
    assert (
        channel.sent[0].body == "꼭 써 주세요" and channel.sent[0].data["review_deadline"] is None
    )


def test_bus_registration_routes_events_and_isolates_handler_failures(caplog):
    bus = InProcessEventDispatcher()
    channel, handlers = build()
    register_handlers(bus, handlers)
    bus.publish(
        MeetingConfirmed(meeting_id=1, student_id=9, staff_id=2, slot_at=START, location="")
    )
    assert len(channel.sent) == 1

    def explode(*args, **kwargs):
        raise RuntimeError("handler bug")

    handlers._service.notify = explode
    bus.publish(
        MeetingConfirmed(meeting_id=2, student_id=9, staff_id=2, slot_at=START, location="")
    )  # 예외 전파 없음
    assert "알림 이벤트 처리 실패" in caplog.text


@pytest.mark.parametrize(
    "location,expected", [("", "10.20 14:00"), ("회의실", "10.20 14:00 · 회의실")]
)
def test_meeting_body_omits_separator_without_location(location, expected):
    channel, h = build()
    h.on_meeting_confirmed(
        MeetingConfirmed(meeting_id=1, student_id=1, staff_id=2, slot_at=START, location=location)
    )
    assert channel.sent[0].body == expected
