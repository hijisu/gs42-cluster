"""운영 도메인 테스트: DB 없이 실행."""

from datetime import date, timedelta

import pytest

from reviews.domain.course import Course, ReviewTarget
from reviews.domain.errors import InvalidCourse, InvalidIntraId
from reviews.domain.participants import parse_intra_ids

D = date(2026, 11, 20)


def course(**kw):
    base = dict(name="과정", start_date=D, end_date=D + timedelta(days=8))
    return Course(**{**base, **kw})


# ── 파싱 ──
def test_parse_handles_csv_newlines_spaces_case_and_dedupes():
    assert parse_intra_ids("Alice, bob\ncarol;  ALICE\n\n") == ["alice", "bob", "carol"]


def test_parse_skips_header_row():
    assert parse_intra_ids("intra_id\nalice\nbob") == ["alice", "bob"]
    assert parse_intra_ids("login,alice") == ["alice"]


def test_parse_empty_is_empty():
    assert parse_intra_ids("  \n ,, ") == []


@pytest.mark.parametrize("bad", ["a", "한글이름", "bob!", "-bob", "x" * 33, "b/c"])
def test_parse_rejects_invalid_ids(bad):
    with pytest.raises(InvalidIntraId):
        parse_intra_ids(f"alice,{bad}")


# ── Course 검증 ──
def test_valid_course_passes():
    course().validate()


@pytest.mark.parametrize(
    "kw",
    [
        {"name": "  "},
        {"end_date": D - timedelta(days=1)},
        {"review_deadline": D + timedelta(days=1)},  # 종료일(D+8)보다 이름
    ],
)
def test_invalid_course_rejected(kw):
    with pytest.raises(InvalidCourse):
        course(**kw).validate()


def test_deadline_on_end_date_is_ok():
    course(review_deadline=D + timedelta(days=8)).validate()


def test_update_changes_fields_and_rolls_back_on_violation():
    c = course()
    c.update(location="온라인", review_deadline=D + timedelta(days=20))
    assert c.location == "온라인" and c.review_deadline == D + timedelta(days=20)
    with pytest.raises(InvalidCourse):
        c.update(end_date=D - timedelta(days=3), name="바뀐 이름")
    assert c.end_date == D + timedelta(days=8) and c.name == "과정"  # 되돌려짐


def test_update_rejects_unknown_fields():
    with pytest.raises(InvalidCourse):
        course().update(participants={"x"})


# ── 참여자 / 요청 대상 ──
def test_add_participants_reports_added_and_existing_and_normalizes():
    c = course(participants={"alice"})
    assert c.add_participants(["Alice", "bob", "BOB", "carol"]) == (
        ["bob", "carol"],
        ["alice", "bob"][:1] + ["bob"],
    )


def test_review_targets_all_and_pending():
    c = course(participants={"alice", "bob", "carol"})
    assert c.review_targets(ReviewTarget.ALL, {"alice"}) == ["alice", "bob", "carol"]
    assert c.review_targets(ReviewTarget.PENDING, {"Alice"}) == ["bob", "carol"]
    assert c.review_targets(ReviewTarget.PENDING, {"alice", "bob", "carol"}) == []


def test_pending_ignores_reviewers_who_are_not_participants():
    assert course(participants={"alice"}).review_targets(ReviewTarget.PENDING, {"zed"}) == ["alice"]


def test_remove_participants_reports_removed_and_missing():
    c = course(participants={"alice", "bob"})
    removed, missing = c.remove_participants(["Alice", "zed"])
    assert removed == ["alice"] and missing == ["zed"]
    assert c.participants == {"bob"}


def test_update_rejects_status_field():
    with pytest.raises(InvalidCourse):
        course().update(status="completed")
