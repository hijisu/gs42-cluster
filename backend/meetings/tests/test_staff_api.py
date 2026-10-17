from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.infrastructure.models import AvailabilitySlot, MeetingRequestRow, MeetingType

pytestmark = pytest.mark.django_db
KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


@pytest.fixture
def staff_client():
    return login("staff")


@pytest.fixture
def student_client():
    return login("student")


@pytest.fixture
def slot_at():
    return (datetime.now(KST) + timedelta(days=3)).replace(
        hour=15, minute=0, second=0, microsecond=0
    )


@pytest.fixture
def meeting(student_client, slot_at):
    staff = User.objects.get(intra_id="staff")
    AvailabilitySlot.objects.create(staff=staff, start_at=slot_at)
    freeze = MeetingType.objects.get(code="freeze")
    response = student_client.post(
        "/api/meetings",
        {"type_id": freeze.pk, "slot_at": slot_at.isoformat(), "content": "문의"},
        format="json",
    )
    return response.json()


def other_staff(name="staff2"):
    return User.objects.create_user(name, name="운영팀 B", role=Role.STAFF.value)


STAFF_URLS = [
    ("get", "/api/staff/meetings"),
    ("patch", "/api/staff/meetings/1/assign"),
    ("post", "/api/staff/meetings/1/confirm"),
    ("post", "/api/staff/meetings/1/propose"),
    ("get", "/api/staff/availability?from=2026-10-12&to=2026-10-13"),
    ("put", "/api/staff/availability"),
    ("get", "/api/staff/meeting-types"),
    ("put", "/api/staff/meeting-types"),
    ("get", "/api/staff/members"),
]


@pytest.mark.parametrize(("method", "url"), STAFF_URLS)
def test_students_get_403_and_anonymous_401(method, url, student_client):
    assert getattr(student_client, method)(url, {}, format="json").status_code == 403
    assert getattr(APIClient(), method)(url, {}, format="json").status_code == 401


def test_list_filters_by_status_and_includes_student(staff_client, meeting):
    rows = staff_client.get("/api/staff/meetings").json()
    assert rows[0]["student"]["intra_id"] == "student" and rows[0]["status"] == "pending"
    assert staff_client.get("/api/staff/meetings?status=confirmed").json() == []
    assert len(staff_client.get("/api/staff/meetings?status=pending").json()) == 1
    assert staff_client.get("/api/staff/meetings?status=bogus").status_code == 400


def test_assign_sets_staff_and_validates_account(staff_client, meeting):
    b = other_staff()
    ok = staff_client.patch(
        f"/api/staff/meetings/{meeting['id']}/assign", {"staff_id": b.pk}, format="json"
    )
    assert ok.status_code == 200 and ok.json()["staff"]["id"] == b.pk
    student = User.objects.get(intra_id="student")
    bad = staff_client.patch(
        f"/api/staff/meetings/{meeting['id']}/assign", {"staff_id": student.pk}, format="json"
    )
    assert bad.status_code == 404 and bad.json()["code"] == "staff_not_found"


def test_confirm_then_student_sees_location_and_slot_closes(
    staff_client, student_client, meeting, slot_at
):
    response = staff_client.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "1층 사무실 앞"}, format="json"
    )
    assert response.status_code == 200
    assert (
        response.json()["status"] == "confirmed" and response.json()["location"] == "1층 사무실 앞"
    )
    mine = student_client.get("/api/meetings/me").json()[0]
    assert mine["status"] == "confirmed" and "staff_note" not in mine
    day = slot_at.date().isoformat()
    slots = student_client.get(f"/api/meetings/slots?from={day}&to={day}").json()
    assert slots[0]["available"] is False


def test_confirm_requires_location(staff_client, meeting):
    assert (
        staff_client.post(
            f"/api/staff/meetings/{meeting['id']}/confirm", {}, format="json"
        ).status_code
        == 400
    )


def test_duplicate_confirm_same_staff_same_slot_409(staff_client, student_client, meeting, slot_at):
    freeze = MeetingType.objects.get(code="freeze")
    second = student_client.post(
        "/api/meetings",
        {"type_id": freeze.pk, "slot_at": slot_at.isoformat(), "content": "두번째"},
        format="json",
    ).json()
    url = "/api/staff/meetings/{}/confirm"
    assert (
        staff_client.post(url.format(meeting["id"]), {"location": "a"}, format="json").status_code
        == 200
    )
    response = staff_client.post(url.format(second["id"]), {"location": "b"}, format="json")
    assert response.status_code == 409 and response.json()["code"] == "slot_unavailable"
    assert MeetingRequestRow.objects.get(pk=second["id"]).status == "pending"


def test_db_constraint_blocks_duplicate_confirmed_rows(staff_client, meeting):
    row = MeetingRequestRow.objects.get(pk=meeting["id"])
    staff = User.objects.get(intra_id="staff")
    MeetingRequestRow.objects.filter(pk=row.pk).update(status="confirmed", staff=staff)
    clone = MeetingRequestRow.objects.create(
        student=row.student, type=row.type, slot_at=row.slot_at, staff=staff, status="pending"
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        MeetingRequestRow.objects.filter(pk=clone.pk).update(status="confirmed")


def test_confirm_twice_is_invalid_transition_409(staff_client, meeting):
    url = f"/api/staff/meetings/{meeting['id']}/confirm"
    staff_client.post(url, {"location": "a"}, format="json")
    again = staff_client.post(url, {"location": "a"}, format="json")
    assert again.status_code == 409 and again.json()["code"] == "invalid_transition"


def test_propose_then_confirm_uses_proposed_time(staff_client, student_client, meeting, slot_at):
    later = (slot_at + timedelta(hours=1)).isoformat()
    proposed = staff_client.post(
        f"/api/staff/meetings/{meeting['id']}/propose",
        {"proposed_at": later, "note": "이 시간 어때요"},
        format="json",
    )
    assert proposed.status_code == 200 and proposed.json()["status"] == "proposed"
    assert student_client.get("/api/meetings/me").json()[0]["proposed_at"] is not None
    confirmed = staff_client.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "회의실"}, format="json"
    ).json()
    assert datetime.fromisoformat(
        confirmed["slot_at"].replace("Z", "+00:00")
    ) == datetime.fromisoformat(later)


def test_propose_rejects_past_but_accepts_arbitrary_minutes(staff_client, meeting, slot_at):
    url = f"/api/staff/meetings/{meeting['id']}/propose"
    past = (datetime.now(KST) - timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    assert (
        staff_client.post(url, {"proposed_at": past.isoformat()}, format="json").status_code == 400
    )
    odd = (slot_at + timedelta(minutes=7)).isoformat()
    assert staff_client.post(url, {"proposed_at": odd}, format="json").status_code == 200


def test_canceled_meeting_cannot_be_confirmed(staff_client, student_client, meeting):
    student_client.post(f"/api/meetings/{meeting['id']}/cancel")
    response = staff_client.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "a"}, format="json"
    )
    assert response.status_code == 409


def test_unknown_meeting_404(staff_client):
    assert (
        staff_client.post(
            "/api/staff/meetings/9999/confirm", {"location": "a"}, format="json"
        ).status_code
        == 404
    )


def test_availability_get_put_roundtrip(staff_client, slot_at):
    day = slot_at.date().isoformat()
    slots = [slot_at, slot_at + timedelta(minutes=30)]
    put = staff_client.put(
        "/api/staff/availability",
        {"from": day, "to": day, "slots": [s.isoformat() for s in slots]},
        format="json",
    )
    assert put.status_code == 200 and len(put.json()["slots"]) == 2
    got = staff_client.get(f"/api/staff/availability?from={day}&to={day}").json()["slots"]
    assert len(got) == 2
    staff_client.put(
        "/api/staff/availability",
        {"from": day, "to": day, "slots": [slots[0].isoformat()]},
        format="json",
    )
    assert (
        len(staff_client.get(f"/api/staff/availability?from={day}&to={day}").json()["slots"]) == 1
    )


def test_availability_only_touches_own_slots(staff_client, slot_at):
    other = other_staff()
    AvailabilitySlot.objects.create(staff=other, start_at=slot_at)
    day = slot_at.date().isoformat()
    staff_client.put(
        "/api/staff/availability", {"from": day, "to": day, "slots": []}, format="json"
    )
    assert AvailabilitySlot.objects.filter(staff=other).count() == 1


def test_availability_rejects_unaligned_and_closing_confirmed(staff_client, meeting, slot_at):
    day = slot_at.date().isoformat()
    bad = staff_client.put(
        "/api/staff/availability",
        {"from": day, "to": day, "slots": [(slot_at + timedelta(minutes=5)).isoformat()]},
        format="json",
    )
    assert bad.status_code == 400
    staff_client.post(
        f"/api/staff/meetings/{meeting['id']}/confirm", {"location": "a"}, format="json"
    )
    blocked = staff_client.put(
        "/api/staff/availability", {"from": day, "to": day, "slots": []}, format="json"
    )
    assert blocked.status_code == 409 and blocked.json()["code"] == "slot_has_meeting"


def test_meeting_types_defaults_get_put(staff_client):
    freeze = MeetingType.objects.get(code="freeze")
    b = other_staff()
    put = staff_client.put(
        "/api/staff/meeting-types", [{"id": freeze.pk, "default_staff_id": b.pk}], format="json"
    )
    assert put.status_code == 200
    by_code = {t["code"]: t for t in staff_client.get("/api/staff/meeting-types").json()}
    assert by_code["freeze"]["default_staff"] == {"id": b.pk, "name": "운영팀 B"}
    assert by_code["other"]["default_staff"] is None
    cleared = staff_client.put(
        "/api/staff/meeting-types", [{"id": freeze.pk, "default_staff_id": None}], format="json"
    )
    assert {t["code"]: t for t in cleared.json()}["freeze"]["default_staff"] is None


def test_meeting_types_put_validates(staff_client, student_client):
    freeze = MeetingType.objects.get(code="freeze")
    student = User.objects.get(intra_id="student")
    assert (
        staff_client.put(
            "/api/staff/meeting-types", [{"id": 9999, "default_staff_id": None}], format="json"
        ).status_code
        == 404
    )
    bad = staff_client.put(
        "/api/staff/meeting-types",
        [{"id": freeze.pk, "default_staff_id": student.pk}],
        format="json",
    )
    assert bad.status_code == 404 and bad.json()["code"] == "staff_not_found"


def test_new_requests_use_default_staff_from_types(staff_client, student_client, slot_at):
    staff = User.objects.get(intra_id="staff")
    AvailabilitySlot.objects.create(staff=staff, start_at=slot_at)
    freeze = MeetingType.objects.get(code="freeze")
    staff_client.put(
        "/api/staff/meeting-types", [{"id": freeze.pk, "default_staff_id": staff.pk}], format="json"
    )
    created = student_client.post(
        "/api/meetings",
        {"type_id": freeze.pk, "slot_at": slot_at.isoformat(), "content": ""},
        format="json",
    ).json()
    assert created["staff"]["id"] == staff.pk


def test_members_lists_staff_only(staff_client):
    other_staff()
    names = {m["intra_id"] for m in staff_client.get("/api/staff/members").json()}
    assert names == {"staff", "staff2"}
