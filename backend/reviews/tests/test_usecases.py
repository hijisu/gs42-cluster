"""유스케이스 테스트: DB 없이 인메모리 구현."""

from datetime import date, timedelta

import pytest

from reviews.application.ports import CourseStats
from reviews.application.usecases import (
    CreateReviewCommand,
    CreateReviewUseCase,
    ListCourseReviewsUseCase,
    ListCoursesUseCase,
    ListTodoReviewsUseCase,
    UpdateReviewCommand,
    UpdateReviewUseCase,
    Viewer,
)
from reviews.domain.course import Course, CourseStatus
from reviews.domain.errors import (
    AlreadyReviewed,
    CourseNotFound,
    InvalidReview,
    NotParticipant,
    NotReviewAuthor,
    ReviewClosed,
    ReviewNotFound,
)

TODAY = date(2026, 11, 27)
ALICE = Viewer(user_id=1, intra_id="alice")
BOB = Viewer(user_id=2, intra_id="bob")


def make_course(id, status=CourseStatus.COMPLETED, participants=("alice", "bob"), deadline=None):
    start, end = {
        CourseStatus.COMPLETED: (0, 0),
        CourseStatus.ONGOING: (-1, 1),
        CourseStatus.UPCOMING: (1, 2),
    }[status]
    return Course(
        id=id,
        name=f"과정{id}",
        start_date=TODAY + timedelta(days=start),
        end_date=TODAY + timedelta(days=end),
        review_deadline=deadline,
        participants=set(participants),
    )


class Courses:
    def __init__(self, *courses):
        self.items = {c.id: c for c in courses}

    def list_all(self):
        return list(self.items.values())

    def get(self, course_id):
        return self.items.get(course_id)


class Reviews:
    def __init__(self):
        self.rows = []

    def add(self, review):
        review.id = len(self.rows) + 1
        self.rows.append(review)
        return review

    def get(self, review_id):
        return next((r for r in self.rows if r.id == review_id), None)

    def save(self, review):
        self.saved = getattr(self, "saved", 0) + 1

    def exists(self, course_id, author_id):
        return any(r.course_id == course_id and r.author_id == author_id for r in self.rows)

    def list_for_course(self, course_id):
        return [r for r in reversed(self.rows) if r.course_id == course_id]

    def reviewed_course_ids(self, author_id):
        return {r.course_id for r in self.rows if r.author_id == author_id}

    def stats_by_course(self):
        out = {}
        for cid in {r.course_id for r in self.rows}:
            ratings = [r.rating for r in self.rows if r.course_id == cid]
            out[cid] = CourseStats(round(sum(ratings) / len(ratings), 1), len(ratings))
        return out


def cmd(viewer=ALICE, **kw):
    base = dict(course_id=1, rating=5, good="좋아요")
    return CreateReviewCommand(viewer=viewer, **{**base, **kw})


@pytest.fixture
def env():
    courses = Courses(
        make_course(1),
        make_course(2, status=CourseStatus.ONGOING),
        make_course(3, participants=("bob",)),
    )
    reviews = Reviews()
    return courses, reviews, CreateReviewUseCase(courses, reviews, lambda: TODAY)


def test_participant_creates_review(env):
    *_, create = env
    item = create.execute(cmd())
    assert item.mine and item.review.id == 1 and item.review.author_intra_id == "alice"


def test_non_participant_forbidden(env):
    *_, create = env
    with pytest.raises(NotParticipant):
        create.execute(cmd(course_id=3))


def test_unknown_course(env):
    *_, create = env
    with pytest.raises(CourseNotFound):
        create.execute(cmd(course_id=99))


def test_closed_course(env):
    *_, create = env
    with pytest.raises(ReviewClosed):
        create.execute(cmd(course_id=2))


def test_deadline_passed_is_closed():
    courses = Courses(make_course(1, deadline=TODAY - timedelta(days=1)))
    with pytest.raises(ReviewClosed):
        CreateReviewUseCase(courses, Reviews(), lambda: TODAY).execute(cmd())


def test_duplicate_blocked_but_other_author_ok(env):
    _, reviews, create = env
    create.execute(cmd())
    with pytest.raises(AlreadyReviewed):
        create.execute(cmd())
    create.execute(cmd(viewer=BOB))
    assert len(reviews.rows) == 2


def test_invalid_rating_saves_nothing(env):
    _, reviews, create = env
    with pytest.raises(InvalidReview):
        create.execute(cmd(rating=9))
    assert reviews.rows == []


def test_anonymous_review_hides_author_for_everyone_but_marks_mine(env):
    courses, reviews, create = env
    create.execute(cmd(anonymous=True))
    lister = ListCourseReviewsUseCase(courses, reviews)
    for viewer, mine in ((ALICE, True), (BOB, False)):
        (item,) = lister.execute(1, viewer)
        assert item.review.author_intra_id is None and item.mine is mine


def test_non_anonymous_review_shows_author(env):
    courses, reviews, create = env
    create.execute(cmd(anonymous=False))
    (item,) = ListCourseReviewsUseCase(courses, reviews).execute(1, BOB)
    assert item.review.author_intra_id == "alice"


def test_list_reviews_unknown_course(env):
    courses, reviews, _ = env
    with pytest.raises(CourseNotFound):
        ListCourseReviewsUseCase(courses, reviews).execute(99, ALICE)


def test_course_list_flags_and_stats(env):
    courses, reviews, create = env
    create.execute(cmd(rating=5))
    create.execute(cmd(viewer=BOB, rating=4))
    by_id = {
        v.course.id: v for v in ListCoursesUseCase(courses, reviews, lambda: TODAY).execute(ALICE)
    }
    assert by_id[1].stats == CourseStats(4.5, 2)
    assert (by_id[1].participating, by_id[1].reviewed, by_id[1].can_review) == (True, True, False)
    assert (by_id[2].participating, by_id[2].can_review) == (True, False)  # 진행 중
    assert (by_id[3].participating, by_id[3].can_review) == (False, False)
    assert by_id[3].stats == CourseStats(None, 0)


def test_todo_lists_unreviewed_open_participated_courses_only(env):
    courses, reviews, create = env
    todo = ListTodoReviewsUseCase(courses, reviews, lambda: TODAY)
    assert [v.course.id for v in todo.execute(ALICE)] == [1]
    create.execute(cmd())
    assert todo.execute(ALICE) == []
    assert [v.course.id for v in todo.execute(BOB)] == [1, 3]


def _written(course=None, deadline=None):
    courses = Courses(course or make_course(1, deadline=deadline))
    reviews = Reviews()
    CreateReviewUseCase(courses, reviews, lambda: TODAY).execute(
        CreateReviewCommand(viewer=ALICE, course_id=1, rating=3, good="원문")
    )
    return courses, reviews


def test_author_updates_own_review_during_review_period():
    courses, reviews = _written()
    update = UpdateReviewUseCase(courses, reviews, lambda: TODAY)
    item = update.execute(
        UpdateReviewCommand(
            viewer=ALICE, review_id=1, changes={"rating": 5, "good": "수정", "anonymous": True}
        )
    )
    assert item.mine and item.review.rating == 5 and item.review.good == "수정"
    assert item.review.author_intra_id is None
    assert reviews.rows[0].rating == 5 and reviews.saved == 1


def test_update_rejects_other_users_missing_review_and_closed_period():
    courses, reviews = _written(deadline=TODAY + timedelta(days=3))
    update = UpdateReviewUseCase(courses, reviews, lambda: TODAY)
    with pytest.raises(NotReviewAuthor):
        update.execute(UpdateReviewCommand(viewer=BOB, review_id=1, changes={"rating": 1}))
    with pytest.raises(ReviewNotFound):
        update.execute(UpdateReviewCommand(viewer=ALICE, review_id=99, changes={"rating": 1}))
    with pytest.raises(InvalidReview):
        update.execute(UpdateReviewCommand(viewer=ALICE, review_id=1, changes={"rating": 0}))
    # 마감일이 지나면 수정할 수 없다
    late = UpdateReviewUseCase(courses, reviews, lambda: TODAY + timedelta(days=4))
    with pytest.raises(ReviewClosed):
        late.execute(UpdateReviewCommand(viewer=ALICE, review_id=1, changes={"rating": 4}))
    assert reviews.rows[0].rating == 3 and getattr(reviews, "saved", 0) == 0


def test_update_requires_still_being_a_participant():
    courses, reviews = _written()
    courses.items[1].participants.discard("alice")
    update = UpdateReviewUseCase(courses, reviews, lambda: TODAY)
    with pytest.raises(NotParticipant):
        update.execute(UpdateReviewCommand(viewer=ALICE, review_id=1, changes={"rating": 4}))
