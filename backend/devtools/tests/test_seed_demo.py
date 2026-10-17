import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
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
    assert AvailabilitySlot.objects.exists() and CourseRow.objects.count() == 3
    assert MeetingType.objects.filter(default_staff__isnull=False).count() == 6
    statuses = sorted(RoomReservationRow.objects.values_list("status", flat=True))
    assert statuses == ["approved", "pending", "pending"]


def test_overlapping_pending_request_is_shown_as_a_conflict_to_staff():
    seed()
    staff = APIClient()
    staff.post("/api/auth/mock-login", {"role": "staff"}, format="json")
    rows = staff.get("/api/staff/reservations?status=pending").json()
    conflicting = [r for r in rows if r["conflict"]]
    assert len(conflicting) == 1 and conflicting[0]["user"]["intra_id"] == "intra_b"
    assert len(conflicting[0]["conflict_ids"]) == 1


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
    ReviewRow.objects.create(course=course, author=student, rating=5, title="내 후기")

    seed("--reset")

    assert not MeetingRequestRow.objects.filter(student=student).exists()
    assert not RoomReservationRow.objects.filter(user=student).exists()
    assert not NotificationRow.objects.filter(user=student).exists()
    assert not ReviewRow.objects.filter(author=student).exists()
    # 다른 교육생과 시드 예약은 그대로
    assert MeetingRequestRow.objects.filter(student=peer).exists()
    assert NotificationRow.objects.filter(user=peer).exists()
    assert RoomReservationRow.objects.filter(user__intra_id__in=["intra_a", "intra_b"]).count() == 3
    assert User.objects.filter(intra_id="staff", role=Role.STAFF.value).exists()
