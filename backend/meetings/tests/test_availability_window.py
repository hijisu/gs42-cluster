from datetime import date, datetime, timedelta

import pytest
from rest_framework.test import APIClient

from meetings.domain.availability_window import (
    ensure_editable,
    ensure_readable,
    last_day,
    week_start,
)
from meetings.domain.defaults import KST
from meetings.domain.errors import AvailabilityBeyondWindow, AvailabilityInPast

WED = date(2026, 10, 14)  # 수요일 → 1주차 월요일 10/12, 4주차 일요일 11/8


def test_window_is_four_weeks_counting_this_week():
    assert week_start(WED) == date(2026, 10, 12)
    assert last_day(WED) == date(2026, 11, 8)
    # 일요일에도 그 주가 1주차다
    assert last_day(date(2026, 10, 18)) == date(2026, 11, 8)
    assert last_day(date(2026, 10, 19)) == date(2026, 11, 15)  # 다음 월요일이면 한 주 밀림


def test_editable_boundaries():
    ensure_editable(WED, WED, WED)  # 오늘
    ensure_editable(WED, date(2026, 11, 8), WED)  # 4주 마지막 날
    with pytest.raises(AvailabilityInPast):
        ensure_editable(WED - timedelta(days=1), WED, WED)
    with pytest.raises(AvailabilityBeyondWindow):
        ensure_editable(WED, date(2026, 11, 9), WED)


def test_readable_allows_the_whole_current_week_for_week_views():
    ensure_readable(date(2026, 10, 12), date(2026, 10, 18), WED)  # 이번 주 월요일부터
    with pytest.raises(AvailabilityInPast):
        ensure_readable(date(2026, 10, 11), date(2026, 10, 18), WED)
    with pytest.raises(AvailabilityBeyondWindow):
        ensure_readable(WED, date(2026, 11, 9), WED)


# ── API ──
@pytest.fixture
def staff_client(settings):
    settings.MOCK_LOGIN_ENABLED = True
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": "staff"}, format="json")
    return client


def today():
    return datetime.now(KST).date()


@pytest.mark.django_db
def test_put_and_delete_reject_past_and_beyond_with_domain_codes(staff_client):
    t = today()
    yesterday, far = t - timedelta(days=1), last_day(t) + timedelta(days=1)

    def put(day):
        return staff_client.put(
            "/api/staff/availability",
            {"from": str(day), "to": str(day), "slots": []},
            format="json",
        )

    assert (
        put(yesterday).status_code == 400 and put(yesterday).json()["code"] == "availability_past"
    )
    assert put(far).status_code == 400 and put(far).json()["code"] == "availability_too_far"
    for day, code in ((yesterday, "availability_past"), (far, "availability_too_far")):
        res = staff_client.delete(f"/api/staff/availability?from={day}&to={day}")
        assert res.status_code == 400 and res.json()["code"] == code


@pytest.mark.django_db
def test_boundary_days_are_accepted(staff_client):
    t = today()
    last = last_day(t)
    ok = staff_client.put(
        "/api/staff/availability", {"from": str(t), "to": str(t), "slots": []}, format="json"
    )
    assert ok.status_code == 200
    assert (
        staff_client.put(
            "/api/staff/availability",
            {"from": str(last), "to": str(last), "slots": []},
            format="json",
        ).status_code
        == 200
    )
    assert staff_client.delete(f"/api/staff/availability?from={t}&to={last}").status_code == 200


@pytest.mark.django_db
def test_get_allows_this_weeks_monday_to_window_end_only(staff_client):
    t = today()
    assert (
        staff_client.get(
            f"/api/staff/availability?from={week_start(t)}&to={last_day(t)}"
        ).status_code
        == 200
        or (last_day(t) - week_start(t)).days > 31
    )
    assert (
        staff_client.get(
            f"/api/staff/availability?from={week_start(t) - timedelta(days=1)}&to={t}"
        ).json()["code"]
        == "availability_past"
    )
    assert (
        staff_client.get(
            f"/api/staff/availability?from={t}&to={last_day(t) + timedelta(days=1)}"
        ).json()["code"]
        == "availability_too_far"
    )
