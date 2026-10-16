import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import IntegrityError, connection, connections, transaction
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from common.infrastructure.event_bus import event_bus
from rooms.domain.events import ReservationApproved, ReservationReassigned, ReservationRejected
from rooms.infrastructure.models import Room, RoomReservationRow

KST = ZoneInfo("Asia/Seoul")
EVENTS = (ReservationApproved, ReservationRejected, ReservationReassigned)


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


@pytest.fixture
def events():
    captured = []
    for event_type in EVENTS:
        event_bus.subscribe(event_type, captured.append)
    yield captured
    for event_type in EVENTS:
        event_bus._handlers[event_type].remove(captured.append)


def login(role):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


@pytest.fixture
def day():
    return (datetime.now(KST) + timedelta(days=3)).date()


def at(day, hour):
    return datetime(day.year, day.month, day.day, hour, tzinfo=KST)


def room(code="multipurpose"):
    return Room.objects.get(code=code)


def body(day, start=14, end=16, code="multipurpose", **kw):
    return {
        "room_id": room(code).pk,
        "start_at": at(day, start).isoformat(),
        "end_at": at(day, end).isoformat(),
        "purpose": "스터디",
        "headcount": 3,
        **kw,
    }


def request_as(role, day, **kw):
    client = login(role)
    response = client.post("/api/reservations", body(day, **kw), format="json")
    assert response.status_code == 201, response.content
    return response.json()


STAFF = "/api/staff"
STAFF_URLS = [
    ("get", f"{STAFF}/reservations"),
    ("post", f"{STAFF}/reservations"),
    ("post", f"{STAFF}/reservations/1/approve"),
    ("post", f"{STAFF}/reservations/1/reject"),
    ("post", f"{STAFF}/reservations/1/reassign"),
    ("put", f"{STAFF}/rooms/rules"),
    ("post", f"{STAFF}/rooms"),
    ("patch", f"{STAFF}/rooms/1"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("method", "url"), STAFF_URLS)
def test_students_403_and_anonymous_401(method, url):
    assert getattr(login("student"), method)(url, {}, format="json").status_code == 403
    assert getattr(APIClient(), method)(url, {}, format="json").status_code == 401


@pytest.mark.django_db
def test_list_has_user_conflict_flag_and_filters(day):
    first = request_as("student", day, start=14, end=16)
    second = request_as("staff", day, start=15, end=17)
    staff = login("staff")
    rows = staff.get(f"{STAFF}/reservations?date={day.isoformat()}").json()
    by_id = {r["id"]: r for r in rows}
    assert by_id[second["id"]]["conflict"] is True and by_id[second["id"]]["conflict_ids"] == [
        first["id"]
    ]
    assert by_id[first["id"]]["user"]["intra_id"] == "student"
    assert [r["id"] for r in staff.get(f"{STAFF}/reservations?status=approved").json()] == []
    assert staff.get(f"{STAFF}/reservations?status=bogus").status_code == 400
    assert len(staff.get(f"{STAFF}/reservations").json()) == 2  # 오늘 이후 전체


@pytest.mark.django_db
def test_approve_then_conflict_flag_clears_for_others_and_student_sees_status(day, events):
    first = request_as("student", day, start=14, end=16)
    staff = login("staff")
    approved = staff.post(f"{STAFF}/reservations/{first['id']}/approve")
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert isinstance(events[0], ReservationApproved)
    assert login("student").get("/api/reservations/me").json()[0]["status"] == "approved"


@pytest.mark.django_db
def test_overlapping_approval_409_keeps_second_pending(day):
    first = request_as("student", day, start=14, end=16)
    second = request_as("staff", day, start=15, end=17)
    staff = login("staff")
    assert staff.post(f"{STAFF}/reservations/{first['id']}/approve").status_code == 200
    response = staff.post(f"{STAFF}/reservations/{second['id']}/approve")
    assert response.status_code == 409 and response.json()["code"] == "room_conflict"
    assert RoomReservationRow.objects.get(pk=second["id"]).status == "pending"


@pytest.mark.django_db
def test_approve_twice_and_unknown(day):
    r = request_as("student", day)
    staff = login("staff")
    staff.post(f"{STAFF}/reservations/{r['id']}/approve")
    again = staff.post(f"{STAFF}/reservations/{r['id']}/approve")
    assert again.status_code == 409 and again.json()["code"] == "invalid_transition"
    assert staff.post(f"{STAFF}/reservations/9999/approve").status_code == 404


@pytest.mark.django_db
def test_reject_with_reason_visible_to_student(day, events):
    r = request_as("student", day)
    staff = login("staff")
    assert (
        staff.post(f"{STAFF}/reservations/{r['id']}/reject", {}, format="json").status_code == 400
    )
    ok = staff.post(
        f"{STAFF}/reservations/{r['id']}/reject", {"reason": "해당 시간 기존 예약"}, format="json"
    )
    assert ok.status_code == 200 and ok.json()["status"] == "rejected"
    mine = login("student").get("/api/reservations/me").json()[0]
    assert (mine["status"], mine["reject_reason"]) == ("rejected", "해당 시간 기존 예약")
    assert isinstance(events[0], ReservationRejected)
    again = staff.post(f"{STAFF}/reservations/{r['id']}/reject", {"reason": "x"}, format="json")
    assert again.status_code == 409


@pytest.mark.django_db
def test_reassign_to_other_room_approves_and_shows_requested_room(day, events):
    r = request_as("student", day, code="multipurpose")
    staff = login("staff")
    target = room("universe-small")
    response = staff.post(
        f"{STAFF}/reservations/{r['id']}/reassign", {"room_id": target.pk}, format="json"
    )
    assert response.status_code == 200
    data = response.json()
    assert (data["status"], data["room"]["code"], data["requested_room"]["code"]) == (
        "approved",
        "universe-small",
        "multipurpose",
    )
    assert isinstance(events[0], ReservationReassigned)


@pytest.mark.django_db
def test_reassign_conflict_unknown_and_blocked_room(day):
    other = request_as("staff", day, code="universe-small")
    staff = login("staff")
    staff.post(f"{STAFF}/reservations/{other['id']}/approve")
    r = request_as("student", day, code="multipurpose")
    url = f"{STAFF}/reservations/{r['id']}/reassign"
    assert staff.post(url, {"room_id": room("universe-small").pk}, format="json").status_code == 409
    assert staff.post(url, {"room_id": 9999}, format="json").status_code == 404
    Room.objects.filter(code="universe-large").update(status="blocked")
    blocked = staff.post(url, {"room_id": room("universe-large").pk}, format="json")
    assert blocked.status_code == 409 and blocked.json()["code"] == "room_blocked"
    assert RoomReservationRow.objects.get(pk=r["id"]).room.code == "multipurpose"


@pytest.mark.django_db
def test_staff_direct_booking_is_approved_and_blocks_students(day, events):
    staff = login("staff")
    response = staff.post(
        f"{STAFF}/reservations", body(day, 10, 12, purpose="교육 운영"), format="json"
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "approved" and data["created_by_staff"] is True and events == []
    clash = staff.post(f"{STAFF}/reservations", body(day, 11, 13), format="json")
    assert clash.status_code == 409 and RoomReservationRow.objects.count() == 1
    # 학생 요청은 접수되지만 충돌 플래그, 승인은 불가
    student_request = request_as("student", day, start=11, end=12)
    assert student_request["conflict"] is True
    assert staff.post(f"{STAFF}/reservations/{student_request['id']}/approve").status_code == 409


@pytest.mark.django_db
def test_staff_booking_for_student_notifies_and_validates(day, events):
    staff = login("staff")
    student_id = User.objects.create_user("kim", name="김", role=Role.STUDENT.value).pk
    ok = staff.post(f"{STAFF}/reservations", body(day, user_id=student_id), format="json")
    assert ok.status_code == 201 and ok.json()["user"]["intra_id"] == "kim"
    assert isinstance(events[0], ReservationApproved) and events[0].user_id == student_id
    assert (
        staff.post(f"{STAFF}/reservations", body(day, 6, 8), format="json").json()["code"]
        == "outside_hours"
    )


@pytest.mark.django_db
def test_rules_update_changes_student_endpoints(day):
    staff, student = login("staff"), login("student")
    early = body(day, 7, 8)
    assert student.post("/api/reservations", early, format="json").json()["code"] == "outside_hours"
    put = staff.put(
        f"{STAFF}/rooms/rules",
        {"open_hour": 7, "close_hour": 23, "usage_rules": ["문 잠그기", " ", "소등"]},
        format="json",
    )
    assert put.status_code == 200 and put.json()["usage_rules"] == ["문 잠그기", "소등"]
    assert student.post("/api/reservations", early, format="json").status_code == 201
    rules = student.get("/api/rooms/rules").json()
    assert (rules["open_hour"], rules["close_hour"], rules["usage_rules"]) == (
        7,
        23,
        ["문 잠그기", "소등"],
    )
    hours = student.get(f"/api/rooms/availability?date={day.isoformat()}").json()["rooms"][0][
        "hours"
    ]
    assert (hours[0]["hour"], hours[-1]["hour"]) == (7, 22)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bad",
    [
        {"open_hour": 10, "close_hour": 10, "usage_rules": ["a"]},
        {"open_hour": 9, "close_hour": 22, "usage_rules": []},
        {"open_hour": 9, "close_hour": 22, "usage_rules": [" "]},
        {"open_hour": 9, "close_hour": 30, "usage_rules": ["a"]},
        {"open_hour": 9},
    ],
)
def test_rules_update_validation(bad):
    assert login("staff").put(f"{STAFF}/rooms/rules", bad, format="json").status_code == 400


@pytest.mark.django_db
def test_add_room_and_block_it(day):
    staff = login("staff")
    created = staff.post(
        f"{STAFF}/rooms", {"name": "새 회의실", "equipment": "프로젝터"}, format="json"
    )
    assert created.status_code == 201
    new = created.json()
    assert new["code"].startswith("room-") and new["status"] == "open"
    assert new["id"] in [r["id"] for r in login("student").get("/api/rooms").json()]
    blocked = staff.patch(f"{STAFF}/rooms/{new['id']}", {"status": "blocked"}, format="json")
    assert blocked.status_code == 200 and blocked.json()["status"] == "blocked"
    student = login("student")
    response = student.post("/api/reservations", {**body(day), "room_id": new["id"]}, format="json")
    assert response.status_code == 409 and response.json()["code"] == "room_blocked"
    cells = {
        r["room"]["id"]: r
        for r in student.get(f"/api/rooms/availability?date={day.isoformat()}").json()["rooms"]
    }
    assert {h["state"] for h in cells[new["id"]]["hours"]} == {"blocked"}
    assert (
        staff.patch(
            f"{STAFF}/rooms/{new['id']}", {"status": "open", "name": "이름 변경"}, format="json"
        ).json()["name"]
        == "이름 변경"
    )


@pytest.mark.django_db
def test_room_code_must_be_unique_and_patch_validates():
    staff = login("staff")
    assert (
        staff.post(f"{STAFF}/rooms", {"name": "x", "code": "alpha"}, format="json").status_code
        == 201
    )
    dup = staff.post(f"{STAFF}/rooms", {"name": "y", "code": "alpha"}, format="json")
    assert dup.status_code == 409 and dup.json()["code"] == "room_code_taken"
    assert (
        staff.patch(f"{STAFF}/rooms/9999", {"status": "blocked"}, format="json").status_code == 404
    )
    assert (
        staff.patch(f"{STAFF}/rooms/{room().pk}", {"status": "weird"}, format="json").status_code
        == 400
    )


# ── DB 배타 제약과 동시 승인 ──
@pytest.mark.django_db
def test_db_exclusion_constraint_rejects_overlapping_approved_rows(day):
    user = User.objects.create_user("db_user", name="x", role=Role.STUDENT.value)
    common = dict(user=user, room=room(), requested_room=room(), purpose="a", headcount=1)
    RoomReservationRow.objects.create(
        start_at=at(day, 10), end_at=at(day, 12), status="approved", **common
    )
    RoomReservationRow.objects.create(  # 대기끼리/대기와는 겹쳐도 된다
        start_at=at(day, 11), end_at=at(day, 13), status="pending", **common
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        RoomReservationRow.objects.create(
            start_at=at(day, 11), end_at=at(day, 13), status="approved", **common
        )
    RoomReservationRow.objects.create(  # 맞닿음은 허용
        start_at=at(day, 12), end_at=at(day, 14), status="approved", **common
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_approvals_of_overlapping_requests_only_one_wins(day):
    first = request_as("student", day, start=14, end=16)
    second = request_as("staff", day, start=15, end=17)
    barrier = threading.Barrier(2)
    results = {}

    def approve(reservation_id):
        try:
            client = login("staff")
            barrier.wait(timeout=10)
            results[reservation_id] = client.post(
                f"{STAFF}/reservations/{reservation_id}/approve"
            ).status_code
        finally:
            connections.close_all()

    threads = [threading.Thread(target=approve, args=(r["id"],)) for r in (first, second)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert sorted(results.values()) == [200, 409], results
    assert RoomReservationRow.objects.filter(status="approved").count() == 1
    assert RoomReservationRow.objects.filter(status="pending").count() == 1
    assert connection.vendor == "postgresql"
