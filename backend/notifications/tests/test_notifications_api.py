from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.infrastructure.models import AvailabilitySlot, MeetingType
from notifications.infrastructure import repositories as notification_repositories
from notifications.infrastructure.models import NotificationRow
from reviews.infrastructure.models import CourseParticipant, CourseRow
from rooms.infrastructure.models import Room

pytestmark = pytest.mark.django_db
KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


def future(hour=14, days=3):
    d = (datetime.now(KST) + timedelta(days=days)).date()
    return datetime(d.year, d.month, d.day, hour, tzinfo=KST)


def student_notifications(client=None):
    return (client or login("student")).get("/api/notifications").json()


def request_meeting(student, staff_user):
    slot = future(15)
    AvailabilitySlot.objects.create(staff=staff_user, start_at=slot)
    kind = MeetingType.objects.get(code="freeze")
    return student.post(
        "/api/meetings",
        {"type_id": kind.pk, "slot_at": slot.isoformat(), "content": "문의"},
        format="json",
    ).json()


def request_room(student, code="multipurpose", hour=14):
    room = Room.objects.get(code=code)
    return student.post(
        "/api/reservations",
        {
            "room_id": room.pk,
            "start_at": future(hour).isoformat(),
            "end_at": future(hour + 2).isoformat(),
            "purpose": "스터디",
            "headcount": 3,
        },
        format="json",
    ).json()


def test_endpoints_require_login():
    for method, url in [
        ("get", "/api/notifications"),
        ("post", "/api/notifications/1/read"),
        ("post", "/api/notifications/read-all"),
    ]:
        assert getattr(APIClient(), method)(url).status_code == 401


def test_empty_list_for_new_user():
    assert student_notifications() == {"unread_count": 0, "items": []}


def test_meeting_confirmed_shows_up_for_the_student():
    student, staff = login("student"), login("staff")
    meeting = request_meeting(student, User.objects.get(intra_id="staff"))
    assert student_notifications(student)["items"] == []  # 신청만으로는 알림 없음
    staff.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "1층 사무실 앞"}, format="json"
    )
    data = student_notifications(student)
    assert data["unread_count"] == 1
    (item,) = data["items"]
    assert (
        item["type"] == "meeting_confirmed" and item["read"] is False and item["link"] == "/meeting"
    )
    assert "1층 사무실 앞" in item["body"] and item["data"]["meeting_id"] == meeting["id"]


def test_staff_who_confirms_gets_no_notification():
    student, staff = login("student"), login("staff")
    meeting = request_meeting(student, User.objects.get(intra_id="staff"))
    staff.post(f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "a"}, format="json")
    assert student_notifications(staff)["items"] == []


def test_meeting_proposed_notifies_the_student():
    student, staff = login("student"), login("staff")
    meeting = request_meeting(student, User.objects.get(intra_id="staff"))
    staff.post(
        f"/api/staff/meetings/{meeting['id']}/propose",
        {"proposed_at": future(16).isoformat()},
        format="json",
    )
    assert student_notifications(student)["items"][0]["type"] == "meeting_proposed"


def test_reservation_approve_reject_and_reassign_notify_the_student():
    student, staff = login("student"), login("staff")
    approved = request_room(student, hour=9)
    rejected = request_room(student, hour=12)
    moved = request_room(student, code="multipurpose", hour=18)
    staff.post(f"/api/staff/reservations/{approved['id']}/approve")
    staff.post(
        f"/api/staff/reservations/{rejected['id']}/reject",
        {"reason": "해당 시간 기존 예약"},
        format="json",
    )
    small = Room.objects.get(code="universe-small")
    staff.post(
        f"/api/staff/reservations/{moved['id']}/reassign", {"room_id": small.pk}, format="json"
    )

    items = student_notifications(student)["items"]
    by_type = {i["type"]: i for i in items}
    assert set(by_type) == {
        "reservation_approved",
        "reservation_rejected",
        "reservation_reassigned",
    }
    assert "다목적회의실" in by_type["reservation_approved"]["body"]
    assert "해당 시간 기존 예약" in by_type["reservation_rejected"]["body"]
    assert "다목적회의실 → 유니버스룸(소)" in by_type["reservation_reassigned"]["body"]
    assert all(i["link"] == "/room" for i in items)
    assert len(items) == 3  # 최신순


def test_reservation_approval_notifies_only_the_owner():
    owner, other, staff = login("student"), APIClient(), login("staff")
    other.post("/api/auth/mock-login", {"role": "student"}, format="json")
    reservation = request_room(owner)
    staff.post(f"/api/staff/reservations/{reservation['id']}/approve")
    assert NotificationRow.objects.count() == 1
    assert NotificationRow.objects.get().user.intra_id == "student"


def test_failed_approval_creates_no_notification():
    student, staff = login("student"), login("staff")
    first = request_room(student)
    second = request_room(staff, hour=15)
    staff.post(f"/api/staff/reservations/{first['id']}/approve")
    NotificationRow.objects.all().delete()
    assert staff.post(f"/api/staff/reservations/{second['id']}/approve").status_code == 409
    assert NotificationRow.objects.count() == 0


def test_review_request_notifies_registered_participants_only():
    staff = login("staff")
    student = login("student")  # 가입된 참여자
    today = timezone.localdate()
    course = CourseRow.objects.create(
        name="파이썬 AI 교육",
        start_date=today - timedelta(days=12),
        end_date=today - timedelta(days=3),
        status="completed",
        review_deadline=today + timedelta(days=7),
    )
    for intra in ("student", "not_signed_up_yet"):
        CourseParticipant.objects.create(course=course, intra_id=intra)
    result = staff.post(
        f"/api/staff/courses/{course.pk}/review-request",
        {"target": "all", "message": "후기 부탁해요"},
        format="json",
    ).json()
    assert result["recipient_count"] == 2
    (item,) = student_notifications(student)["items"]
    assert item["type"] == "review_requested" and item["link"] == "/reviews"
    assert item["title"] == "파이썬 AI 교육 후기를 남겨 주세요" and item["body"].startswith(
        "후기 부탁해요"
    )
    assert NotificationRow.objects.count() == 1


def test_list_filters_unread_limits_and_counts():
    student, staff = login("student"), login("staff")
    user = User.objects.get(intra_id="student")
    for i in range(4):
        NotificationRow.objects.create(user=user, type="meeting_confirmed", title=f"n{i}")
    all_items = student.get("/api/notifications").json()
    assert all_items["unread_count"] == 4 and [i["title"] for i in all_items["items"]] == [
        "n3",
        "n2",
        "n1",
        "n0",
    ]
    assert len(student.get("/api/notifications?limit=2").json()["items"]) == 2
    first = all_items["items"][0]["id"]
    student.post(f"/api/notifications/{first}/read")
    unread = student.get("/api/notifications?unread=true").json()
    assert unread["unread_count"] == 3 and len(unread["items"]) == 3
    assert student.get("/api/notifications?limit=0").status_code == 400
    assert student.get("/api/notifications?limit=999").status_code == 400
    assert staff.get("/api/notifications").json()["items"] == []


def test_mark_read_is_idempotent_and_returns_item():
    student = login("student")
    row = NotificationRow.objects.create(
        user=User.objects.get(intra_id="student"), type="meeting_confirmed", title="t"
    )
    first = student.post(f"/api/notifications/{row.pk}/read")
    assert first.status_code == 200 and first.json()["read"] is True
    again = student.post(f"/api/notifications/{row.pk}/read")
    assert again.json()["read_at"] == first.json()["read_at"]


def test_cannot_read_or_discover_someone_elses_notification():
    login("student")
    staff = login("staff")
    row = NotificationRow.objects.create(
        user=User.objects.get(intra_id="student"), type="meeting_confirmed", title="비공개"
    )
    response = staff.post(f"/api/notifications/{row.pk}/read")
    assert response.status_code == 404 and response.json()["code"] == "notification_not_found"
    assert NotificationRow.objects.get(pk=row.pk).read_at is None
    assert staff.post("/api/notifications/9999/read").status_code == 404


def test_read_all_marks_only_my_unread():
    student, staff = login("student"), login("staff")
    mine, theirs = User.objects.get(intra_id="student"), User.objects.get(intra_id="staff")
    for _ in range(3):
        NotificationRow.objects.create(user=mine, type="meeting_confirmed", title="m")
    NotificationRow.objects.create(user=theirs, type="meeting_confirmed", title="t")
    assert student.post("/api/notifications/read-all").json() == {"updated": 3}
    assert student.get("/api/notifications").json()["unread_count"] == 0
    assert staff.get("/api/notifications").json()["unread_count"] == 1
    assert student.post("/api/notifications/read-all").json() == {"updated": 0}


def test_a_broken_notification_channel_never_breaks_the_staff_action(monkeypatch):
    def broken(self, notification):
        raise RuntimeError("DB가 알림을 저장하지 못함")

    monkeypatch.setattr(notification_repositories.InAppNotifier, "send", broken)
    student, staff = login("student"), login("staff")
    meeting = request_meeting(student, User.objects.get(intra_id="staff"))
    response = staff.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "a"}, format="json"
    )
    assert response.status_code == 200 and response.json()["status"] == "confirmed"
    assert NotificationRow.objects.count() == 0


def test_a_failed_insert_does_not_poison_the_request_transaction(monkeypatch):
    """알림 INSERT가 DB 오류로 즉시 실패해도 savepoint 덕분에 면담 확정은 커밋된다."""

    def failing_add(self, notification):
        NotificationRow.objects.create(
            user=User.objects.get(intra_id="student"), type="meeting_confirmed", title=None
        )

    monkeypatch.setattr(notification_repositories.DjangoNotificationRepository, "add", failing_add)
    student, staff = login("student"), login("staff")
    meeting = request_meeting(student, User.objects.get(intra_id="staff"))
    response = staff.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "a"}, format="json"
    )
    assert response.status_code == 200 and response.json()["status"] == "confirmed"
    assert staff.get("/api/staff/meetings?status=confirmed").json()[0]["id"] == meeting["id"]


def test_no_staff_role_is_required_to_read_notifications():
    assert Role.STUDENT.value == "student"
    assert login("student").get("/api/notifications").status_code == 200
    assert login("staff").get("/api/notifications").status_code == 200
