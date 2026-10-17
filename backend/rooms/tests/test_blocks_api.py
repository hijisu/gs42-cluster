from datetime import datetime, timedelta

import pytest
from rest_framework.test import APIClient

from rooms.domain.rules import KST
from rooms.infrastructure.models import Room, RoomBlockRow, RoomReservationRow

pytestmark = pytest.mark.django_db

SAT = datetime(2030, 1, 12, tzinfo=KST)  # 토요일


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


@pytest.fixture
def room():
    return Room.objects.first() or Room.objects.create(code="r1", name="유니버스룸(대)")


@pytest.fixture
def staff():
    return login("staff")


@pytest.fixture
def student():
    return login("student")


def weekly(room, **over):
    body = {
        "room_id": room.pk,
        "start_at": SAT.replace(hour=10).isoformat(),
        "end_at": SAT.replace(hour=12).isoformat(),
        "reason": "수학 교육",
        "repeat": "weekly",
        "weekdays": [5],
        "until": "2030-02-09",
    }
    return {**body, **over}


def test_endpoints_require_staff(student, room):
    for method, url in [
        ("get", "/api/staff/room-blocks?from=2030-01-01&to=2030-01-31"),
        ("post", "/api/staff/room-blocks"),
        ("patch", "/api/staff/room-blocks/1"),
        ("delete", "/api/staff/room-blocks/1"),
        ("delete", "/api/staff/room-blocks/1/occurrences/2030-01-12"),
    ]:
        assert getattr(student, method)(url, {}, format="json").status_code == 403, url
    assert (
        APIClient().get("/api/staff/room-blocks?from=2030-01-01&to=2030-01-31").status_code == 401
    )


def test_create_weekly_block_and_list_occurrences(staff, room):
    res = staff.post("/api/staff/room-blocks", weekly(room), format="json")
    assert res.status_code == 201
    data = res.json()
    assert data["saved"] is True and data["conflicting_reservations"] == []
    assert [o["date"] for o in data["block"]["occurrences"]] == [
        "2030-01-12", "2030-01-19", "2030-01-26", "2030-02-02", "2030-02-09",
    ]  # fmt: skip

    listed = staff.get("/api/staff/room-blocks?from=2030-01-14&to=2030-01-27").json()
    assert len(listed) == 1
    assert [o["date"] for o in listed[0]["occurrences"]] == ["2030-01-19", "2030-01-26"]
    assert staff.get("/api/staff/room-blocks?from=2030-03-01&to=2030-03-31").json() == []
    assert (
        staff.get(
            f"/api/staff/room-blocks?from=2030-01-01&to=2030-01-31&room_id={room.pk + 99}"
        ).json()
        == []
    )


def test_validation_errors(staff, room):
    bad = staff.post("/api/staff/room-blocks", weekly(room, until=None), format="json")
    assert bad.status_code == 400 and bad.json()["code"] == "invalid_block"
    assert (
        staff.post("/api/staff/room-blocks", weekly(room, reason=" "), format="json").status_code
        == 400
    )
    assert (
        staff.post(
            "/api/staff/room-blocks", weekly(room, room_id=999999), format="json"
        ).status_code
        == 404
    )
    assert (
        staff.post(
            "/api/staff/room-blocks", weekly(room, repeat="monthly"), format="json"
        ).status_code
        == 400
    )
    inverted = weekly(
        room, start_at=SAT.replace(hour=12).isoformat(), end_at=SAT.replace(hour=10).isoformat()
    )
    assert staff.post("/api/staff/room-blocks", inverted, format="json").status_code == 400
    assert RoomBlockRow.objects.count() == 0


def test_reservation_overlapping_a_block_occurrence_is_rejected(staff, student, room):
    staff.post("/api/staff/room-blocks", weekly(room), format="json")
    body = {
        "room_id": room.pk,
        "start_at": SAT.replace(day=19, hour=11).isoformat(),
        "end_at": SAT.replace(day=19, hour=13).isoformat(),
        "purpose": "스터디",
        "headcount": 3,
    }
    res = student.post("/api/reservations", body, format="json")
    assert res.status_code == 409 and res.json()["code"] == "room_block_conflict"
    # 차단 회차가 아닌 시간(맞닿음, 다른 요일)은 가능
    touching = {
        **body,
        "start_at": SAT.replace(day=19, hour=12).isoformat(),
        "end_at": SAT.replace(day=19, hour=13).isoformat(),
    }
    assert student.post("/api/reservations", touching, format="json").status_code == 201
    sunday = {
        **body,
        "start_at": SAT.replace(day=20, hour=11).isoformat(),
        "end_at": SAT.replace(day=20, hour=12).isoformat(),
    }
    assert student.post("/api/reservations", sunday, format="json").status_code == 201


def test_block_creation_warns_about_existing_reservations_but_still_saves(staff, student, room):
    body = {
        "room_id": room.pk,
        "start_at": SAT.replace(day=19, hour=10, minute=30).isoformat(),
        "end_at": SAT.replace(day=19, hour=11, minute=30).isoformat(),
        "purpose": "스터디",
        "headcount": 2,
    }
    reservation_id = student.post("/api/reservations", body, format="json").json()["id"]

    preview = staff.post(
        "/api/staff/room-blocks", {**weekly(room), "check_only": True}, format="json"
    )
    assert preview.status_code == 200 and preview.json()["saved"] is False
    assert [r["id"] for r in preview.json()["conflicting_reservations"]] == [reservation_id]
    assert RoomBlockRow.objects.count() == 0

    saved = staff.post("/api/staff/room-blocks", weekly(room), format="json")
    assert saved.status_code == 201
    assert [r["id"] for r in saved.json()["conflicting_reservations"]] == [reservation_id]
    # 기존 예약은 자동으로 바뀌지 않는다
    assert RoomReservationRow.objects.get(pk=reservation_id).status == "pending"
    # 하지만 이제 그 예약은 승인할 수 없다
    approve = staff.post(f"/api/staff/reservations/{reservation_id}/approve")
    assert approve.status_code == 409 and approve.json()["code"] == "room_block_conflict"


def test_staff_direct_booking_cannot_overlap_a_block(staff, room):
    staff.post("/api/staff/room-blocks", weekly(room), format="json")
    body = {
        "room_id": room.pk,
        "start_at": SAT.replace(day=12, hour=10).isoformat(),
        "end_at": SAT.replace(day=12, hour=11).isoformat(),
        "purpose": "운영팀",
        "headcount": 1,
    }
    res = staff.post("/api/staff/reservations", body, format="json")
    assert res.status_code == 409 and res.json()["code"] == "room_block_conflict"
    assert RoomReservationRow.objects.count() == 0


def test_availability_marks_blocked_hours_and_lists_closed_periods(staff, student, room):
    staff.post("/api/staff/room-blocks", weekly(room), format="json")
    data = student.get("/api/rooms/availability?date=2030-01-19").json()
    item = next(r for r in data["rooms"] if r["room"]["id"] == room.pk)
    states = {h["hour"]: h["state"] for h in item["hours"]}
    assert states[10] == "blocked" and states[11] == "blocked" and states[12] != "blocked"
    assert [c["reason"] for c in item["closed"]] == ["수학 교육"]
    other_day = student.get("/api/rooms/availability?date=2030-01-18").json()
    assert next(r for r in other_day["rooms"] if r["room"]["id"] == room.pk)["closed"] == []


def test_delete_one_occurrence_and_whole_series(staff, student, room):
    block_id = staff.post("/api/staff/room-blocks", weekly(room), format="json").json()["block"][
        "id"
    ]
    assert (
        staff.delete(f"/api/staff/room-blocks/{block_id}/occurrences/2030-01-19").status_code == 204
    )
    days = [
        o["date"]
        for o in staff.get("/api/staff/room-blocks?from=2030-01-01&to=2030-02-28").json()[0][
            "occurrences"
        ]
    ]
    assert "2030-01-19" not in days and len(days) == 4
    missing = staff.delete(f"/api/staff/room-blocks/{block_id}/occurrences/2030-01-20")
    assert missing.status_code == 400 and missing.json()["code"] == "invalid_block"
    assert (
        staff.delete(f"/api/staff/room-blocks/{block_id}/occurrences/not-a-date").status_code == 400
    )

    assert staff.delete(f"/api/staff/room-blocks/{block_id}").status_code == 204
    assert staff.delete(f"/api/staff/room-blocks/{block_id}").status_code == 404
    assert RoomBlockRow.objects.count() == 0


def test_deleting_the_last_occurrence_removes_the_series(staff, room):
    single = {k: v for k, v in weekly(room).items() if k not in ("repeat", "weekdays", "until")}
    block_id = staff.post("/api/staff/room-blocks", single, format="json").json()["block"]["id"]
    assert (
        staff.delete(f"/api/staff/room-blocks/{block_id}/occurrences/2030-01-12").status_code == 204
    )
    assert RoomBlockRow.objects.count() == 0


def test_update_series_and_single_occurrence(staff, room):
    block_id = staff.post("/api/staff/room-blocks", weekly(room), format="json").json()["block"][
        "id"
    ]

    series = staff.patch(
        f"/api/staff/room-blocks/{block_id}",
        {
            "start_at": SAT.replace(hour=13).isoformat(),
            "end_at": SAT.replace(hour=15).isoformat(),
            "reason": "수학(오후)",
        },
        format="json",
    )
    assert series.status_code == 200
    first = series.json()["block"]["occurrences"][0]
    assert (
        first["start_at"].startswith("2030-01-12T13:00")
        and series.json()["block"]["reason"] == "수학(오후)"
    )
    assert (
        staff.patch(
            f"/api/staff/room-blocks/{block_id}", {"reason": " "}, format="json"
        ).status_code
        == 400
    )
    assert (
        staff.patch("/api/staff/room-blocks/999999", {"reason": "x"}, format="json").status_code
        == 404
    )

    one = staff.patch(
        f"/api/staff/room-blocks/{block_id}/occurrences/2030-01-19",
        {
            "start_at": SAT.replace(day=19, hour=9).isoformat(),
            "end_at": SAT.replace(day=19, hour=10).isoformat(),
            "reason": "특강",
        },
        format="json",
    )
    assert one.status_code == 200 and one.json()["block"]["repeat"] == "none"
    assert RoomBlockRow.objects.count() == 2
    listed = staff.get("/api/staff/room-blocks?from=2030-01-19&to=2030-01-19").json()
    assert sorted((b["reason"], b["occurrences"][0]["start_at"][11:16]) for b in listed) == [
        ("특강", "09:00")
    ]
    # 원래 시리즈의 1/19 회차는 빠졌고 나머지는 그대로
    series_days = [
        o["date"]
        for o in staff.get("/api/staff/room-blocks?from=2030-01-01&to=2030-02-28").json()[0][
            "occurrences"
        ]
    ]
    assert "2030-01-19" not in series_days


def test_update_check_only_does_not_save(staff, room):
    block_id = staff.post("/api/staff/room-blocks", weekly(room), format="json").json()["block"][
        "id"
    ]
    res = staff.patch(
        f"/api/staff/room-blocks/{block_id}",
        {"reason": "바뀐 이름", "check_only": True},
        format="json",
    )
    assert res.status_code == 200 and res.json()["saved"] is False
    assert RoomBlockRow.objects.get(pk=block_id).reason == "수학 교육"


def test_existing_reservation_flow_unchanged_without_blocks(student, room):
    body = {
        "room_id": room.pk,
        "start_at": (datetime.now(KST) + timedelta(days=2))
        .replace(hour=10, minute=0, second=0, microsecond=0)
        .isoformat(),
        "end_at": (datetime.now(KST) + timedelta(days=2))
        .replace(hour=11, minute=0, second=0, microsecond=0)
        .isoformat(),
        "purpose": "스터디",
        "headcount": 2,
    }
    assert student.post("/api/reservations", body, format="json").status_code == 201
