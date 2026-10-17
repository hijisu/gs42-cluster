"""교육생 면담 격자(#153): 평일 운영 시간 전체와 칸 상태(open/full/unavailable)."""

from datetime import datetime, timedelta

import pytest
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.domain.defaults import KST
from meetings.domain.slots import SlotAvailability
from meetings.infrastructure.models import (
    AvailabilityCustomDay,
    AvailabilitySlot,
    MeetingRequestRow,
    MeetingType,
)

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=KST)


def test_state_is_derived_from_remaining_and_offered():
    t = NOW + timedelta(days=1)
    assert SlotAvailability(t, remaining=2, offered=2).state == "open"
    assert SlotAvailability(t, remaining=0, offered=2).state == "full"
    assert SlotAvailability(t, remaining=0, offered=0).state == "unavailable"


_today = datetime.now(KST).date()
NEXT_MON = _today - timedelta(days=_today.weekday()) + timedelta(days=7)  # 다음 주 월요일


def student_client(settings):
    settings.MOCK_LOGIN_ENABLED = True
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": "student"}, format="json")
    return client


def slot_map(client, first, last):
    data = client.get(f"/api/meetings/slots?from={first}&to={last}").json()
    return {datetime.fromisoformat(s["start_at"]): s for s in data}


def at(day, hour, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=KST)


@pytest.mark.django_db
def test_grid_returns_every_weekday_operating_slot_even_without_staff(settings):
    client = student_client(settings)  # 스태프가 한 명도 없다 → 전부 '불가'
    week = slot_map(client, NEXT_MON, NEXT_MON + timedelta(days=6))
    assert len(week) == 5 * 12  # 평일 5일 × (10~12, 13~17시 30분 슬롯)
    assert all(s["state"] == "unavailable" and s["available"] is False for s in week.values())
    assert not any(t.weekday() >= 5 for t in week)  # 주말 없음
    assert at(NEXT_MON, 10) in week and at(NEXT_MON, 12) not in week  # 점심 시간은 빠짐


@pytest.mark.django_db
def test_default_staff_makes_slots_open_and_confirmation_makes_them_full(settings):
    staff = User.objects.create_user("st1", name="스태프", role=Role.STAFF.value)
    student = User.objects.create_user("stu1", name="학생", role=Role.STUDENT.value)
    client = student_client(settings)
    grid = slot_map(client, NEXT_MON, NEXT_MON)
    assert all(s["state"] == "open" and s["remaining"] == 1 for s in grid.values())

    MeetingRequestRow.objects.create(
        student=student,
        type=MeetingType.objects.first(),
        slot_at=at(NEXT_MON, 10),
        content="x",
        status="confirmed",
        staff=staff,
    )
    grid = slot_map(client, NEXT_MON, NEXT_MON)
    assert grid[at(NEXT_MON, 10)]["state"] == "full"
    assert grid[at(NEXT_MON, 10, 30)]["state"] == "open"


@pytest.mark.django_db
def test_closed_day_is_unavailable_and_extra_slots_outside_hours_are_included(settings):
    staff = User.objects.create_user("st2", name="스태프", role=Role.STAFF.value)
    AvailabilityCustomDay.objects.create(staff=staff, day=NEXT_MON)  # 이 날은 직접 설정(전부 닫음)
    AvailabilitySlot.objects.create(
        staff=staff, start_at=at(NEXT_MON, 19)
    )  # 운영 시간 밖에 연 시간
    client = student_client(settings)
    grid = slot_map(client, NEXT_MON, NEXT_MON + timedelta(days=1))
    assert grid[at(NEXT_MON, 10)]["state"] == "unavailable"
    assert grid[at(NEXT_MON, 19)]["state"] == "open"
    assert grid[at(NEXT_MON + timedelta(days=1), 10)]["state"] == "open"  # 다음 날은 기본값


@pytest.mark.django_db
def test_response_keeps_legacy_fields_and_is_sorted(settings):
    User.objects.create_user("st3", name="스태프", role=Role.STAFF.value)
    data = student_client(settings).get(f"/api/meetings/slots?from={NEXT_MON}&to={NEXT_MON}").json()
    assert set(data[0]) == {"start_at", "state", "available", "remaining"}
    assert [s["start_at"] for s in data] == sorted(s["start_at"] for s in data)
