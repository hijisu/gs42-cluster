import io
from collections import Counter
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from devtools.management.commands.seed_demo import PEERS, TYPE_STAFF
from meetings.infrastructure.models import AvailabilitySlot, MeetingRequestRow, MeetingType
from notifications.infrastructure.models import NotificationRow
from reviews.infrastructure.models import CourseRow, ReviewRow
from rooms.infrastructure.models import Room, RoomReservationRow

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _debug(settings):
    settings.DEBUG = True
    settings.MOCK_LOGIN_ENABLED = True


def seed(*args):
    call_command("seed_demo", *args, stdout=io.StringIO())


def test_refuses_outside_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        seed()
    assert AvailabilitySlot.objects.count() == 0


def test_seeds_everything_needed_for_the_demo():
    seed()
    assert CourseRow.objects.count() == 3
    assert MeetingType.objects.filter(default_staff__isnull=False).count() == 6
    statuses = Counter(RoomReservationRow.objects.values_list("status", flat=True))
    assert statuses == {"approved": 6, "pending": 7, "rejected": 1}


def test_overlapping_pending_request_is_shown_as_a_conflict_to_staff():
    seed()
    staff = APIClient()
    staff.post("/api/auth/mock-login", {"role": "staff"}, format="json")
    rows = staff.get("/api/staff/reservations?status=pending").json()
    conflicting = [r for r in rows if r["conflict"]]
    # 기본 예시(intra_b)와 영상용 겹침 예시(intra_e)가 충돌로 표시된다
    assert {r["user"]["intra_id"] for r in conflicting} == {"intra_b", "intra_e"}
    assert all(r["conflict_ids"] for r in conflicting)


def test_running_twice_does_not_duplicate_anything():
    seed()
    before = (
        AvailabilitySlot.objects.count(),
        RoomReservationRow.objects.count(),
        CourseRow.objects.count(),
        User.objects.count(),
    )
    seed()
    assert before == (
        AvailabilitySlot.objects.count(),
        RoomReservationRow.objects.count(),
        CourseRow.objects.count(),
        User.objects.count(),
    )


def test_reset_clears_only_the_mock_accounts_data():
    seed()
    student = User.objects.create_user("student", name="모의 교육생", role=Role.STUDENT.value)
    peer = User.objects.get(intra_id="intra_a")
    room, kind = Room.objects.first(), MeetingType.objects.first()
    course = CourseRow.objects.first()
    for user in (student, peer):
        MeetingRequestRow.objects.create(
            student=user, type=kind, slot_at="2030-01-07T01:00:00Z", content="x"
        )
        NotificationRow.objects.create(user=user, type="meeting_confirmed", title="t")
    RoomReservationRow.objects.create(
        user=student,
        room=room,
        requested_room=room,
        start_at="2030-01-07T01:00:00Z",
        end_at="2030-01-07T03:00:00Z",
        purpose="x",
        headcount=1,
    )
    ReviewRow.objects.filter(author=student).delete()
    ReviewRow.objects.create(course=course, author=student, rating=5)

    seed("--reset")

    assert not MeetingRequestRow.objects.filter(student=student).exists()
    assert not RoomReservationRow.objects.filter(user=student).exists()
    assert not NotificationRow.objects.filter(user=student).exists()
    assert not ReviewRow.objects.filter(author=student).exists()
    # 시연 교육생의 데이터는 처음 상태로 다시 만들어지고, 그 밖의 것은 그대로
    assert not MeetingRequestRow.objects.filter(student=peer, slot_at="2030-01-07T01:00:00Z")
    assert not NotificationRow.objects.filter(user=peer).exists()
    assert MeetingRequestRow.objects.filter(student__intra_id__in=PEERS).count() == 12
    assert RoomReservationRow.objects.filter(user__intra_id__in=PEERS).count() == 14
    assert User.objects.filter(intra_id="staff", role=Role.STAFF.value).exists()


def student_client():
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": "student"}, format="json")
    return client


def test_showcase_staff_types_and_sparse_availability():
    seed()
    staff = User.objects.filter(role=Role.STAFF.value)
    assert {u.name for u in staff if u.intra_id != "staff"} == {f"운영팀{n}" for n in range(1, 6)}
    # 유형 6종의 기본 담당자가 서로 다르다
    owners = {
        t.code: t.default_staff.intra_id
        for t in MeetingType.objects.select_related("default_staff")
    }
    assert owners == TYPE_STAFF and len(set(owners.values())) == 6
    # 담당자별로 직접 저장한 가능 시간은 근무 칸(70칸/주)의 약 20%
    per_week = AvailabilitySlot.objects.filter(staff__intra_id="staff1").count() / 4
    assert 10 <= per_week <= 18


def test_slots_differ_by_meeting_type_in_the_showcase():
    seed()
    client = student_client()
    day = timezone.localdate()
    url = f"/api/meetings/slots?from={day}&to={day + timedelta(days=27)}"
    open_by_type = {}
    for t in MeetingType.objects.all():
        data = client.get(f"{url}&type_id={t.id}").json()
        open_by_type[t.code] = {s["start_at"] for s in data if s["state"] == "open"}
    assert all(open_by_type.values())
    assert len({frozenset(v) for v in open_by_type.values()}) == 6


def test_showcase_meeting_requests_cover_the_staff_scenarios():
    seed()
    rows = MeetingRequestRow.objects.exclude(student__intra_id="student")
    assert Counter(rows.values_list("status", flat=True)) == {
        "pending": 8,
        "proposed": 1,
        "confirmed": 2,
        "completed": 1,
    }
    # 처리 대기 요청의 희망 시각은 배정 담당자가 열어 둔 시간이라 그대로 확정할 수 있다
    for row in rows.filter(status="pending"):
        assert AvailabilitySlot.objects.filter(staff=row.staff, start_at=row.slot_at).exists()
    # 같은 담당자·같은 시각 대기 요청(충돌 예시)이 한 쌍 있다
    pairs = Counter(rows.filter(status="pending").values_list("staff_id", "slot_at"))
    assert sorted(pairs.values()).count(2) == 1
    # 영상에서 새로 신청할 모의 교육생은 깨끗하게 시작한다
    assert not MeetingRequestRow.objects.filter(student__intra_id="student").exists()
    assert not RoomReservationRow.objects.filter(user__intra_id="student").exists()


def test_reset_restores_changed_showcase_data():
    seed()
    MeetingRequestRow.objects.filter(status="pending").update(status="canceled")
    MeetingType.objects.filter(code="freeze").update(default_staff=None)
    seed("--reset")
    assert MeetingRequestRow.objects.filter(status="pending").count() == 8
    assert MeetingType.objects.get(code="freeze").default_staff.intra_id == "staff1"
