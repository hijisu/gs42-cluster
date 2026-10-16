from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from reviews.application.ports import CourseRepository, CourseStats, ReviewRepository
from reviews.domain.course import Course
from reviews.domain.errors import AlreadyReviewed, CourseNotFound
from reviews.domain.review import PublicReview, Review

Today = Callable[[], date]


@dataclass(frozen=True)
class Viewer:
    user_id: int
    intra_id: str


@dataclass(frozen=True)
class CourseView:
    course: Course
    stats: CourseStats
    participating: bool
    reviewed: bool
    can_review: bool


@dataclass(frozen=True)
class ReviewItem:
    review: PublicReview
    mine: bool


@dataclass(frozen=True)
class CreateReviewCommand:
    viewer: Viewer
    course_id: int
    rating: int
    title: str
    good: str = ""
    bad: str = ""
    recommend_to: str = ""
    tags: list[str] = field(default_factory=list)
    anonymous: bool = False


class _CourseViews:
    def __init__(self, courses: CourseRepository, reviews: ReviewRepository, today: Today) -> None:
        self._courses = courses
        self._reviews = reviews
        self._today = today

    def build(self, viewer: Viewer) -> list[CourseView]:
        stats = self._reviews.stats_by_course()
        reviewed = self._reviews.reviewed_course_ids(viewer.user_id)
        today = self._today()
        return [
            CourseView(
                course=c,
                stats=stats.get(c.id, CourseStats(None, 0)),
                participating=c.is_participant(viewer.intra_id),
                reviewed=c.id in reviewed,
                can_review=c.can_review(viewer.intra_id, today) and c.id not in reviewed,
            )
            for c in self._courses.list_all()
        ]


class ListCoursesUseCase(_CourseViews):
    def execute(self, viewer: Viewer) -> list[CourseView]:
        return self.build(viewer)


class ListTodoReviewsUseCase(_CourseViews):
    """내가 참여했고, 후기를 받는 중이며, 아직 쓰지 않은 과정."""

    def execute(self, viewer: Viewer) -> list[CourseView]:
        return [v for v in self.build(viewer) if v.can_review]


class ListCourseReviewsUseCase:
    def __init__(self, courses: CourseRepository, reviews: ReviewRepository) -> None:
        self._courses = courses
        self._reviews = reviews

    def execute(self, course_id: int, viewer: Viewer) -> list[ReviewItem]:
        if self._courses.get(course_id) is None:
            raise CourseNotFound("교육과정을 찾을 수 없습니다")
        return [
            ReviewItem(review=r.public_view(), mine=r.author_id == viewer.user_id)
            for r in self._reviews.list_for_course(course_id)
        ]


class CreateReviewUseCase:
    def __init__(self, courses: CourseRepository, reviews: ReviewRepository, today: Today) -> None:
        self._courses = courses
        self._reviews = reviews
        self._today = today

    def execute(self, cmd: CreateReviewCommand) -> ReviewItem:
        course = self._courses.get(cmd.course_id)
        if course is None:
            raise CourseNotFound("교육과정을 찾을 수 없습니다")
        course.ensure_can_review(cmd.viewer.intra_id, self._today())
        if self._reviews.exists(course.id, cmd.viewer.user_id):
            raise AlreadyReviewed("이미 후기를 작성했습니다")
        review = Review(
            course_id=course.id,
            author_id=cmd.viewer.user_id,
            author_intra_id=cmd.viewer.intra_id,
            rating=cmd.rating,
            title=cmd.title,
            good=cmd.good,
            bad=cmd.bad,
            recommend_to=cmd.recommend_to,
            tags=cmd.tags,
            anonymous=cmd.anonymous,
        )
        saved = self._reviews.add(review)
        return ReviewItem(review=saved.public_view(), mine=True)
