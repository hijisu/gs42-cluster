from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.infrastructure.models import AvailabilitySlot, MeetingRequestRow, MeetingType

pytestmark = pytest.mark.django_db
KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


@pytest.fixture
def staff():
    return User.objects.create_user("staff1", name="스태프 A", role=Role.STAFF.value)


@pytest.fixture
def slot_at(staff):
    start = (datetime.now(KST) + timedelta(days=2)).replace(
        hour=15, minute=0, second=0, microsecond=0
    )
    AvailabilitySlot.objects.create(staff=staff, start_at=start)
    return start


def login(role="student"):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


def freeze():
    return MeetingType.objects.get(code="freeze")


def body(slot_at, **kw):
    return {"type_id": freeze().id, "slot_at": slot_at.isoformat(), "content": "문의", **kw}


def test_requires_login():
    for url in (
        "/api/meetings/types",
        "/api/meetings/me",
        "/api/meetings/slots?from=2026-10-12&to=2026-10-13",
    ):
        assert APIClient().get(url).status_code == 401
    assert APIClient().post("/api/meetings", {}, format="json").status_code == 401


def test_six_seeded_types_in_order():
    codes = [t["code"] for t in login().get("/api/meetings/types").json()]
    assert codes == ["freeze", "other-program", "dormitory", "assignment", "military", "other"]


def test_slots_available_then_closed_after_confirm(slot_at, staff):
    client = login()
    day = slot_at.date().isoformat()
    url = f"/api/meetings/slots?from={day}&to={day}"
    (slot,) = client.get(url).json()
    assert slot["available"] is True and slot["remaining"] == 1

    created = client.post("/api/meetings", body(slot_at), format="json").json()
    assert client.get(url).json()[0]["available"] is True  # pending은 자리를 막지 않는다

    MeetingRequestRow.objects.filter(pk=created["id"]).update(status="confirmed", staff=staff)
    assert client.get(url).json()[0]["available"] is False


def test_slots_query_validation():
    client = login()
    assert client.get("/api/meetings/slots").status_code == 400
    assert client.get("/api/meetings/slots?from=2026-10-13&to=2026-10-12").status_code == 400
    assert client.get("/api/meetings/slots?from=2026-01-01&to=2026-12-31").status_code == 400


def test_create_returns_201_with_status_code_and_default_staff(slot_at, staff):
    MeetingType.objects.filter(code="freeze").update(default_staff=staff)
    response = login().post("/api/meetings", body(slot_at, notify_slack=True), format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["type"]["code"] == "freeze"
    assert data["staff"] == {"id": staff.pk, "name": "스태프 A"}
    assert data["notify_slack"] is True


def test_create_without_default_staff_is_unassigned(slot_at):
    data = login().post("/api/meetings", body(slot_at), format="json").json()
    assert data["staff"] is None


def test_create_unavailable_slot_409(slot_at):
    response = login().post("/api/meetings", body(slot_at + timedelta(hours=1)), format="json")
    assert response.status_code == 409 and response.json()["code"] == "slot_unavailable"


def test_create_unaligned_time_400(slot_at):
    response = login().post("/api/meetings", body(slot_at + timedelta(minutes=7)), format="json")
    assert response.status_code == 400 and response.json()["code"] == "invalid_slot"


def test_create_unknown_type_404(slot_at):
    payload = {**body(slot_at), "type_id": 9999}
    assert login().post("/api/meetings", payload, format="json").status_code == 404


def test_create_validation_400():
    assert login().post("/api/meetings", {"type_id": 1}, format="json").status_code == 400


def test_me_lists_only_own_meetings_newest_first(slot_at, staff):
    AvailabilitySlot.objects.create(staff=staff, start_at=slot_at + timedelta(days=1))
    mine = login()
    first = mine.post("/api/meetings", body(slot_at), format="json").json()
    second = mine.post("/api/meetings", body(slot_at + timedelta(days=1)), format="json").json()
    other = APIClient()
    other.post("/api/auth/mock-login", {"role": "staff"}, format="json")  # 다른 사용자
    other.post("/api/meetings", body(slot_at), format="json")
    assert [m["id"] for m in mine.get("/api/meetings/me").json()] == [second["id"], first["id"]]
    assert len(other.get("/api/meetings/me").json()) == 1


def test_cancel_own_then_again_409(slot_at):
    client = login()
    created = client.post("/api/meetings", body(slot_at), format="json").json()
    response = client.post(f"/api/meetings/{created['id']}/cancel")
    assert response.status_code == 200 and response.json()["status"] == "canceled"
    again = client.post(f"/api/meetings/{created['id']}/cancel")
    assert again.status_code == 409 and again.json()["code"] == "invalid_transition"


def test_cancel_other_students_meeting_403(slot_at):
    created = login().post("/api/meetings", body(slot_at), format="json").json()
    intruder = login("staff")
    response = intruder.post(f"/api/meetings/{created['id']}/cancel")
    assert response.status_code == 403
    assert MeetingRequestRow.objects.get(pk=created["id"]).status == "pending"


def test_cancel_unknown_404():
    assert login().post("/api/meetings/9999/cancel").status_code == 404


def test_cancel_confirmed_frees_the_slot(slot_at, staff):
    client = login()
    created = client.post("/api/meetings", body(slot_at), format="json").json()
    MeetingRequestRow.objects.filter(pk=created["id"]).update(status="confirmed", staff=staff)
    day = slot_at.date().isoformat()
    url = f"/api/meetings/slots?from={day}&to={day}"
    assert client.get(url).json()[0]["available"] is False
    client.post(f"/api/meetings/{created['id']}/cancel")
    assert client.get(url).json()[0]["available"] is True
