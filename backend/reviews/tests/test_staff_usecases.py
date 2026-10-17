"""운영 유스케이스 테스트: DB 없이 인메모리 구현."""

import copy
from datetime import date, timedelta

import pytest

from common.infrastructure.dispatcher import InProcessEventDispatcher
from reviews.application.staff_usecases import (
    AddParticipantsUseCase,
    CreateCourseCommand,
    CreateCourseUseCase,
    ListStaffCoursesUseCase,
    RequestReviewsUseCase,
    UpdateCourseUseCase,
)
from reviews.domain.course import Course, CourseStatus, ReviewTarget
from reviews.domain.errors import CourseNotFound, InvalidCourse, InvalidIntraId, ReviewClosed
from reviews.domain.events import ReviewRequested

TODAY = date(2026, 11, 27)


class Courses:
    def __init__(self):
        self.rows: dict[int, Course] = {}

    def add(self, course):
        course.id = len(self.rows) + 1
        self.rows[course.id] = copy.deepcopy(course)
        return course

    def save(self, course):
        self.rows[course.id] = copy.deepcopy(course)

    def get(self, course_id):
        row = self.rows.get(course_id)
        return copy.deepcopy(row) if row else None

    def list_all(self):
        return [copy.deepcopy(c) for c in self.rows.values()]


class Reviews:
    def __init__(self):
        self.by_course: dict[int, set[str]] = {}

    def reviewer_intra_ids_by_course(self):
        return self.by_course


@pytest.fixture
def env():
    courses, reviews, events = Courses(), Reviews(), []
    bus = InProcessEventDispatcher()
    bus.subscribe(ReviewRequested, events.append)
    return courses, reviews, events, bus


def create(env, **kw):
    courses, reviews, *_ = env
    base = dict(
        name="파이썬 AI 교육",
        start_date=TODAY - timedelta(days=12),
        end_date=TODAY - timedelta(days=3),
        review_deadline=TODAY + timedelta(days=7),
        csv="alice,bob\ncarol",
    )
    if kw.pop("status", None) == CourseStatus.ONGOING:  # 상태는 날짜로 계산된다
        base.update(start_date=TODAY - timedelta(days=2), end_date=TODAY + timedelta(days=3))
    return CreateCourseUseCase(courses, reviews).execute(CreateCourseCommand(**{**base, **kw}))


def test_create_registers_course_with_normalized_participants(env):
    view = create(env, csv="", intra_ids=["Alice", "bob", "ALICE"])
    assert view.course.id == 1 and view.course.participants == {"alice", "bob"}
    assert (view.participant_count, view.reviewed_count, view.review_rate) == (2, 0, 0.0)


def test_create_accepts_csv_text_with_header(env):
    assert create(env, csv="intra_id\nalice\nbob").participant_count == 2


@pytest.mark.parametrize(
    ("kw", "error"),
    [
        ({"name": " "}, InvalidCourse),
        ({"end_date": TODAY - timedelta(days=30)}, InvalidCourse),
        ({"csv": "alice,bad id!"}, InvalidIntraId),
    ],
)
def test_create_rejects_invalid_input_and_saves_nothing(env, kw, error):
    with pytest.raises(error):
        create(env, **kw)
    assert env[0].rows == {}


def test_review_rate_counts_only_participants_who_reviewed(env):
    view = create(env)
    env[1].by_course[view.course.id] = {"alice", "zed"}  # zed는 참여자가 아님
    (listed,) = ListStaffCoursesUseCase(env[0], env[1]).execute()
    assert (listed.participant_count, listed.reviewed_count, listed.review_rate) == (3, 1, 0.33)


def test_review_rate_is_none_without_participants(env):
    assert create(env, csv="").review_rate is None


def test_add_participants_reports_added_and_existing(env):
    course_id = create(env, csv="alice").course.id
    result = AddParticipantsUseCase(env[0], env[1]).execute(course_id, csv="alice\nbob,carol")
    assert (result.added, result.existing) == (["bob", "carol"], ["alice"])
    assert result.view.participant_count == 3
    assert env[0].rows[course_id].participants == {"alice", "bob", "carol"}


def test_add_participants_invalid_id_changes_nothing(env):
    course_id = create(env, csv="alice").course.id
    with pytest.raises(InvalidIntraId):
        AddParticipantsUseCase(env[0], env[1]).execute(course_id, csv="bob,???")
    assert env[0].rows[course_id].participants == {"alice"}


def test_add_participants_unknown_course(env):
    with pytest.raises(CourseNotFound):
        AddParticipantsUseCase(env[0], env[1]).execute(99, csv="alice")


def test_update_dates_open_reviews_and_rollback_on_invalid(env):
    course_id = create(env, status=CourseStatus.ONGOING).course
    assert not course_id.is_open_for_review(TODAY)
    update = UpdateCourseUseCase(env[0], env[1])
    view = update.execute(course_id.id, {"end_date": TODAY - timedelta(days=1)})
    assert view.course.is_open_for_review(TODAY)
    course_id = course_id.id
    with pytest.raises(InvalidCourse):
        update.execute(course_id, {"end_date": TODAY - timedelta(days=99)})
    assert env[0].rows[course_id].end_date == TODAY - timedelta(days=1)


def request_uc(env):
    courses, reviews, _, bus = env
    return RequestReviewsUseCase(courses, reviews, bus, lambda: TODAY)


def test_request_all_sends_to_every_participant_and_emits_event(env):
    course_id = create(env).course.id
    env[1].by_course[course_id] = {"alice"}
    result = request_uc(env).execute(course_id, ReviewTarget.ALL, "써 주세요")
    assert result.recipients == ["alice", "bob", "carol"]
    event = env[2][0]
    assert event.intra_ids == ("alice", "bob", "carol") and event.message == "써 주세요"
    assert event.course_name == "파이썬 AI 교육" and event.review_deadline == TODAY + timedelta(
        days=7
    )


def test_request_pending_excludes_those_who_already_reviewed(env):
    course_id = create(env).course.id
    env[1].by_course[course_id] = {"alice", "bob"}
    result = request_uc(env).execute(course_id, ReviewTarget.PENDING)
    assert result.recipients == ["carol"] and env[2][0].intra_ids == ("carol",)


def test_request_with_no_recipients_emits_nothing(env):
    course_id = create(env, csv="alice").course.id
    env[1].by_course[course_id] = {"alice"}
    assert request_uc(env).execute(course_id, ReviewTarget.PENDING).recipients == []
    assert env[2] == []


@pytest.mark.parametrize(
    "kw",
    [{"status": CourseStatus.ONGOING}, {"review_deadline": TODAY - timedelta(days=1)}],
)
def test_request_requires_course_open_for_review(env, kw):
    course_id = create(env, **kw).course.id
    with pytest.raises(ReviewClosed):
        request_uc(env).execute(course_id, ReviewTarget.ALL)
    assert env[2] == []


def test_create_merges_list_and_csv_and_skips_header_only_in_csv(env):
    view = create(env, csv="intra_id\nBob, carol", intra_ids=["alice", "BOB"])
    assert view.course.participants == {"alice", "bob", "carol"}
