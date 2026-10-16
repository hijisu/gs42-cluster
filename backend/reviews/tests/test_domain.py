"""도메인 테스트: DB 없이 실행."""

from datetime import date, timedelta

import pytest

from reviews.domain.course import Course, CourseStatus
from reviews.domain.errors import InvalidReview, NotParticipant, ReviewClosed
from reviews.domain.review import Review

TODAY = date(2026, 11, 27)


def course(
    status=CourseStatus.COMPLETED, deadline=TODAY + timedelta(days=7), participants=("alice",)
):
    return Course(
        id=1,
        name="과정",
        start_date=TODAY - timedelta(days=10),
        end_date=TODAY - timedelta(days=1),
        status=status,
        review_deadline=deadline,
        participants=set(participants),
    )


def review(**kw):
    base = dict(course_id=1, author_id=1, author_intra_id="alice", rating=4, title="좋아요")
    return Review(**{**base, **kw})


# ── Course.can_review ──
def test_participant_can_review_completed_course():
    assert course().can_review("alice", TODAY)


def test_participant_match_ignores_case_and_whitespace():
    assert course(participants=("alice",)).is_participant("ALICE")


def test_non_participant_cannot_review():
    c = course()
    assert not c.can_review("bob", TODAY)
    with pytest.raises(NotParticipant):
        c.ensure_can_review("bob", TODAY)


@pytest.mark.parametrize("status", [CourseStatus.UPCOMING, CourseStatus.ONGOING])
def test_course_not_completed_is_closed(status):
    c = course(status=status)
    assert not c.can_review("alice", TODAY)
    with pytest.raises(ReviewClosed):
        c.ensure_can_review("alice", TODAY)


def test_deadline_day_is_inclusive_and_next_day_is_closed():
    c = course(deadline=TODAY)
    assert c.can_review("alice", TODAY)
    assert not c.can_review("alice", TODAY + timedelta(days=1))


def test_no_deadline_means_always_open_when_completed():
    assert course(deadline=None).can_review("alice", TODAY + timedelta(days=365))


def test_participant_check_comes_before_closed_check():
    with pytest.raises(NotParticipant):
        course(status=CourseStatus.UPCOMING).ensure_can_review("bob", TODAY)


# ── Review ──
@pytest.mark.parametrize("rating", [0, 6, -1])
def test_rating_must_be_1_to_5(rating):
    with pytest.raises(InvalidReview):
        review(rating=rating)


def test_title_required():
    with pytest.raises(InvalidReview):
        review(title="   ")


def test_tags_are_normalized_and_limited():
    assert review(tags=["#인프라 입문", " 실습 ", "#", "실습", ""]).tags == ["인프라 입문", "실습"]
    with pytest.raises(InvalidReview):
        review(tags=[f"t{i}" for i in range(6)])
    with pytest.raises(InvalidReview):
        review(tags=["x" * 21])


def test_public_view_shows_author_when_not_anonymous():
    assert review(id=1, anonymous=False).public_view().author_intra_id == "alice"


def test_public_view_hides_author_when_anonymous():
    view = review(id=1, anonymous=True).public_view()
    assert view.author_intra_id is None and view.anonymous is True
    assert "alice" not in repr(view)  # 어떤 필드에도 작성자 정보가 없다
