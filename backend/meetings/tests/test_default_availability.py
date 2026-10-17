from datetime import date, datetime, timedelta

import pytest
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.domain.defaults import KST, default_slots
from meetings.infrastructure.models import AvailabilityCustomDay, AvailabilitySlot, MeetingType

MONDAY = date(2030, 1, 7)  # 평일(월)
SATURDAY = date(2030, 1, 12)


def day_range(day: date, days: int = 1):
    start = datetime(day.year, day.month, day.day, tzinfo=KST)
    return start, start + timedelta(days=days) - timedelta(microseconds=1)


def times(slots):
    return [s.astimezone(KST).strftime("%H:%M") for s in slots]


# ── 도메인(DB 없음) ──────────────────────────────────────────────


def test_weekday_default_is_10_to_12_and_13_to_17_in_30_minute_slots():
    slots = default_slots(*day_range(MONDAY))
    assert times(slots) == [
        "10:00", "10:30", "11:00", "11:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    ]  # fmt: skip


def test_weekend_has_no_default_slots():
    assert default_slots(*day_range(SATURDAY, days=2)) == []


def test_range_is_inclusive_and_spans_days():
    start, end = day_range(MONDAY, days=7)
    slots = default_slots(start, end)
    assert len(slots) == 12 * 5  # 월~금 5일
    assert default_slots(start + timedelta(hours=16, minutes=30), end)[0] == slots[11]
    only = datetime(2030, 1, 7, 10, 0, tzinfo=KST)
    assert default_slots(only, only) == [only]


# ── API ─────────────────────────────────────────────────────────


@pytest.fixture
def staff_client(settings):
    settings.MOCK_LOGIN_ENABLED = True
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": "staff"}, format="json")
    return client


def get_slots(client, day=MONDAY, to=None):
    to = to or day
    return client.get(f"/api/staff/availability?from={day}&to={to}").json()


@pytest.mark.django_db
def test_every_staff_gets_default_availability_without_setup(staff_client):
    data = get_slots(staff_client)
    assert len(data["slots"]) == 12 and data["customized_days"] == []
    assert get_slots(staff_client, SATURDAY)["slots"] == []


@pytest.mark.django_db
def test_students_see_defaults_as_offered_slots(settings):
    User.objects.create_user("staff9", name="다른 스태프", role=Role.STAFF.value)
    settings.MOCK_LOGIN_ENABLED = True
    student = APIClient()
    student.post("/api/auth/mock-login", {"role": "student"}, format="json")
    # 미래 날짜(2030)는 지난 시간이 아니므로 남은 자리가 있다
    slots = student.get(f"/api/meetings/slots?from={MONDAY}&to={MONDAY}").json()
    assert len(slots) == 12 and all(s["available"] and s["remaining"] == 1 for s in slots)


@pytest.mark.django_db
def test_saving_a_day_customizes_only_that_day(staff_client):
    start = datetime(2030, 1, 7, 10, 0, tzinfo=KST)
    staff_client.put(
        "/api/staff/availability",
        {"from": "2030-01-07", "to": "2030-01-07", "slots": [start.isoformat()]},
        format="json",
    )
    monday = get_slots(staff_client)
    assert times(map(datetime.fromisoformat, monday["slots"])) == ["10:00"]
    assert monday["customized_days"] == ["2030-01-07"]
    # 다음 날(화)은 여전히 기본값
    assert len(get_slots(staff_client, date(2030, 1, 8))["slots"]) == 12


@pytest.mark.django_db
def test_saving_an_empty_day_closes_it_without_losing_other_days(staff_client):
    staff_client.put(
        "/api/staff/availability",
        {"from": "2030-01-07", "to": "2030-01-07", "slots": []},
        format="json",
    )
    assert get_slots(staff_client)["slots"] == []
    assert len(get_slots(staff_client, date(2030, 1, 8))["slots"]) == 12


@pytest.mark.django_db
def test_reset_returns_range_to_defaults(staff_client):
    staff_client.put(
        "/api/staff/availability",
        {"from": "2030-01-07", "to": "2030-01-07", "slots": []},
        format="json",
    )
    res = staff_client.delete("/api/staff/availability?from=2030-01-07&to=2030-01-07")
    assert res.status_code == 200
    assert len(res.json()["slots"]) == 12 and res.json()["customized_days"] == []
    assert not AvailabilityCustomDay.objects.exists()


@pytest.mark.django_db
def test_reset_cannot_close_a_slot_with_a_confirmed_meeting(staff_client):
    me = User.objects.get(intra_id="staff")
    odd = datetime(2030, 1, 7, 20, 0, tzinfo=KST)  # 기본 시간 밖(저녁)에 직접 열어 둔 시간
    staff_client.put(
        "/api/staff/availability",
        {"from": "2030-01-07", "to": "2030-01-07", "slots": [odd.isoformat()]},
        format="json",
    )
    from meetings.infrastructure.models import MeetingRequestRow

    student = User.objects.create_user("stu", name="학생", role=Role.STUDENT.value)
    MeetingRequestRow.objects.create(
        student=student,
        type=MeetingType.objects.first(),
        slot_at=odd,
        content="x",
        status="confirmed",
        staff=me,
    )
    res = staff_client.delete("/api/staff/availability?from=2030-01-07&to=2030-01-07")
    assert res.status_code == 409 and res.json()["code"] == "slot_has_meeting"
    assert AvailabilitySlot.objects.filter(staff=me, start_at=odd).exists()  # 롤백됨


@pytest.mark.django_db
def test_availability_requires_staff(settings):
    settings.MOCK_LOGIN_ENABLED = True
    student = APIClient()
    student.post("/api/auth/mock-login", {"role": "student"}, format="json")
    assert student.get("/api/staff/availability?from=2030-01-07&to=2030-01-07").status_code == 403
    assert (
        student.delete("/api/staff/availability?from=2030-01-07&to=2030-01-07").status_code == 403
    )


@pytest.mark.django_db
def test_migration_preserves_existing_custom_slots():
    """이미 저장해 둔 슬롯이 있는 날은 직접 설정한 날로 남아 기본값이 덮어쓰지 않는다."""
    from importlib import import_module

    from django.apps import apps

    staff = User.objects.create_user("old", name="기존", role=Role.STAFF.value)
    AvailabilitySlot.objects.create(staff=staff, start_at=datetime(2030, 1, 7, 10, 0, tzinfo=KST))
    AvailabilitySlot.objects.create(staff=staff, start_at=datetime(2030, 1, 7, 11, 0, tzinfo=KST))
    import_module("meetings.migrations.0004_availability_custom_day").preserve_existing_slots(
        apps, None
    )
    assert list(AvailabilityCustomDay.objects.values_list("staff_id", "day")) == [
        (staff.pk, MONDAY)
    ]
