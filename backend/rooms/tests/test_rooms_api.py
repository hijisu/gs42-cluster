from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from rest_framework.test import APIClient

from rooms.infrastructure.models import Room, RoomReservationRow

pytestmark = pytest.mark.django_db
KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role="student"):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


@pytest.fixture
def day():
    return (datetime.now(KST) + timedelta(days=3)).date()


def at(day, hour, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=KST)


def room(code="multipurpose"):
    return Room.objects.get(code=code)


def body(day, start=14, end=16, code="multipurpose", **kw):
    return {
        "room_id": room(code).pk,
        "start_at": at(day, start).isoformat(),
        "end_at": at(day, end).isoformat(),
        "purpose": "프로젝트 회의",
        "headcount": 3,
        **kw,
    }


def test_all_endpoints_require_login():
    for method, url in [
        ("get", "/api/rooms"),
        ("get", "/api/rooms/rules"),
        ("get", "/api/rooms/availability?date=2026-10-20"),
        ("get", "/api/reservations/me"),
        ("post", "/api/reservations"),
        ("post", "/api/reservations/1/cancel"),
    ]:
        assert getattr(APIClient(), method)(url).status_code == 401


def test_rooms_seeded_in_order():
    data = login().get("/api/rooms").json()
    assert [r["code"] for r in data] == ["multipurpose", "universe-large", "universe-small"]
    assert data[0]["status"] == "open"


def test_rules_endpoint():
    data = login().get("/api/rooms/rules").json()
    assert (data["open_hour"], data["close_hour"], data["step_minutes"]) == (9, 22, 30)
    assert len(data["usage_rules"]) >= 5


def test_create_returns_201_pending(day):
    response = login().post("/api/reservations", body(day), format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending" and data["conflict"] is False
    assert data["room"]["code"] == data["requested_room"]["code"] == "multipurpose"
    assert data["headcount"] == 3 and data["reject_reason"] == ""


def test_overlapping_request_is_accepted_with_conflict_flag(day):
    login().post("/api/reservations", body(day), format="json")
    second = login().post("/api/reservations", body(day, 15, 17), format="json")
    assert second.status_code == 201 and second.json()["conflict"] is True


def test_adjacent_request_has_no_conflict(day):
    login().post("/api/reservations", body(day, 14, 16), format="json")
    assert (
        login().post("/api/reservations", body(day, 16, 18), format="json").json()["conflict"]
        is False
    )


@pytest.mark.parametrize(
    ("overrides", "status", "code"),
    [
        ({"start": 8, "end": 10}, 400, "outside_hours"),
        ({"start": 21, "end": 23}, 400, "outside_hours"),
        ({"start": 16, "end": 14}, 400, "invalid_range"),
    ],
)
def test_invalid_times_rejected(day, overrides, status, code):
    response = login().post("/api/reservations", body(day, **overrides), format="json")
    assert response.status_code == status and response.json()["code"] == code


def test_past_time_rejected():
    past = (datetime.now(KST) - timedelta(days=1)).date()
    response = login().post("/api/reservations", body(past), format="json")
    assert response.status_code == 400 and response.json()["code"] == "past_time"


def test_unaligned_minutes_rejected(day):
    payload = {**body(day), "start_at": at(day, 14, 10).isoformat()}
    assert (
        login().post("/api/reservations", payload, format="json").json()["code"] == "invalid_range"
    )


def test_unknown_and_blocked_room(day):
    unknown = {**body(day), "room_id": 9999}
    assert login().post("/api/reservations", unknown, format="json").status_code == 404
    Room.objects.filter(code="multipurpose").update(status="blocked")
    blocked = login().post("/api/reservations", body(day), format="json")
    assert blocked.status_code == 409 and blocked.json()["code"] == "room_blocked"


@pytest.mark.parametrize("bad", [{"headcount": 0}, {"purpose": ""}, {"headcount": 1000}])
def test_field_validation(day, bad):
    assert login().post("/api/reservations", {**body(day), **bad}, format="json").status_code == 400


def test_nothing_saved_on_rejection(day):
    login().post("/api/reservations", body(day, 8, 10), format="json")
    assert RoomReservationRow.objects.count() == 0


def test_me_lists_only_own_newest_first(day):
    mine = login()
    first = mine.post("/api/reservations", body(day, 10, 11), format="json").json()
    second = mine.post("/api/reservations", body(day, 14, 15), format="json").json()
    login("staff").post("/api/reservations", body(day, 18, 19), format="json")
    assert [r["id"] for r in mine.get("/api/reservations/me").json()] == [second["id"], first["id"]]


def test_me_marks_conflicting_pending(day):
    login("staff").post("/api/reservations", body(day), format="json")
    mine = login()
    mine.post("/api/reservations", body(day), format="json")
    assert mine.get("/api/reservations/me").json()[0]["conflict"] is True


def test_cancel_own_then_again_409(day):
    client = login()
    created = client.post("/api/reservations", body(day), format="json").json()
    ok = client.post(f"/api/reservations/{created['id']}/cancel")
    assert ok.status_code == 200 and ok.json()["status"] == "canceled"
    again = client.post(f"/api/reservations/{created['id']}/cancel")
    assert again.status_code == 409 and again.json()["code"] == "invalid_transition"


def test_cancel_other_users_reservation_403(day):
    created = login().post("/api/reservations", body(day), format="json").json()
    response = login("staff").post(f"/api/reservations/{created['id']}/cancel")
    assert response.status_code == 403
    assert RoomReservationRow.objects.get(pk=created["id"]).status == "pending"


def test_cancel_unknown_404():
    assert login().post("/api/reservations/9999/cancel").status_code == 404


def test_availability_cells_and_blocks(day):
    client = login()
    mine = client.post("/api/reservations", body(day, 10, 12), format="json").json()
    login("staff").post(
        "/api/reservations", body(day, 14, 15, code="universe-small"), format="json"
    )
    RoomReservationRow.objects.filter(pk=mine["id"]).update(status="approved")
    data = client.get(f"/api/rooms/availability?date={day.isoformat()}").json()
    assert data["date"] == day.isoformat()
    rooms = {r["room"]["code"]: r for r in data["rooms"]}
    hours = {h["hour"]: h["state"] for h in rooms["multipurpose"]["hours"]}
    assert (hours[9], hours[10], hours[11], hours[12]) == ("free", "approved", "approved", "free")
    assert sorted(hours) == list(range(9, 22))
    small = rooms["universe-small"]
    assert {h["hour"]: h["state"] for h in small["hours"]}[14] == "pending"
    assert (
        small["reservations"][0]["mine"] is False
        and rooms["multipurpose"]["reservations"][0]["mine"] is True
    )
    assert "user" not in small["reservations"][0]


def test_availability_ignores_canceled_and_rejected(day):
    client = login()
    created = client.post("/api/reservations", body(day), format="json").json()
    client.post(f"/api/reservations/{created['id']}/cancel")
    data = client.get(f"/api/rooms/availability?date={day.isoformat()}").json()
    assert all(h["state"] == "free" for r in data["rooms"] for h in r["hours"])


def test_availability_blocked_room_and_validation(day):
    Room.objects.filter(code="universe-large").update(status="blocked")
    client = login()
    data = client.get(f"/api/rooms/availability?date={day.isoformat()}").json()
    large = next(r for r in data["rooms"] if r["room"]["code"] == "universe-large")
    assert {h["state"] for h in large["hours"]} == {"blocked"}
    assert client.get("/api/rooms/availability").status_code == 400
    assert client.get("/api/rooms/availability?date=nope").status_code == 400
