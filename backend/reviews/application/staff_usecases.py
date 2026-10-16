"""교육운영팀용 유스케이스."""

from dataclasses import dataclass, field
from datetime import date

from common.domain.events import EventDispatcher
from reviews.application.ports import CourseRepository, ReviewRepository
from reviews.application.usecases import Today
from reviews.domain.course import Course, CourseStatus, ReviewTarget
from reviews.domain.errors import CourseNotFound, ReviewClosed
from reviews.domain.events import ReviewRequested
from reviews.domain.participants import parse_intra_ids


@dataclass(frozen=True)
class StaffCourseView:
    course: Course
    reviewed: set[str]  # 후기를 쓴 참여자 intra_id

    @property
    def participant_count(self) -> int:
        return len(self.course.participants)

    @property
    def reviewed_count(self) -> int:
        return len(self.reviewed & self.course.participants)

    @property
    def review_rate(self) -> float | None:
        if not self.participant_count:
            return None
        return round(self.reviewed_count / self.participant_count, 2)


@dataclass(frozen=True)
class ReviewRequestResult:
    course_id: int
    target: ReviewTarget
    recipients: list[str]


@dataclass(frozen=True)
class AddParticipantsResult:
    view: StaffCourseView
    added: list[str]
    existing: list[str]


def _load(courses: CourseRepository, course_id: int) -> Course:
    course = courses.get(course_id)
    if course is None:
        raise CourseNotFound("교육과정을 찾을 수 없습니다")
    return course


class _Views:
    def __init__(self, courses: CourseRepository, reviews: ReviewRepository) -> None:
        self._courses = courses
        self._reviews = reviews

    def view(self, course: Course) -> StaffCourseView:
        return StaffCourseView(
            course, self._reviews.reviewer_intra_ids_by_course().get(course.id, set())
        )


@dataclass(frozen=True)
class CreateCourseCommand:
    name: str
    start_date: date
    end_date: date
    location: str = ""
    intro: str = ""
    status: CourseStatus = CourseStatus.UPCOMING
    review_deadline: date | None = None
    intra_ids: list[str] = field(default_factory=list)
    csv: str = ""


def _ids(intra_ids: list[str], csv: str = "") -> list[str]:
    """CSV 텍스트와 ID 목록을 각각 파싱·검증한 뒤 합친다(헤더 줄은 CSV 쪽에서만 건너뛴다)."""
    merged = parse_intra_ids(csv) + parse_intra_ids("\n".join(intra_ids))
    return list(dict.fromkeys(merged))


class CreateCourseUseCase(_Views):
    def execute(self, cmd: CreateCourseCommand) -> StaffCourseView:
        course = Course(
            name=cmd.name.strip(),
            start_date=cmd.start_date,
            end_date=cmd.end_date,
            location=cmd.location,
            intro=cmd.intro,
            status=cmd.status,
            review_deadline=cmd.review_deadline,
            participants=set(_ids(cmd.intra_ids, cmd.csv)),
        )
        course.validate()
        return self.view(self._courses.add(course))


class UpdateCourseUseCase(_Views):
    def execute(self, course_id: int, changes: dict) -> StaffCourseView:
        course = _load(self._courses, course_id)
        course.update(**changes)
        self._courses.save(course)
        return self.view(course)


class ListStaffCoursesUseCase(_Views):
    def execute(self) -> list[StaffCourseView]:
        reviewed = self._reviews.reviewer_intra_ids_by_course()
        return [StaffCourseView(c, reviewed.get(c.id, set())) for c in self._courses.list_all()]


class GetStaffCourseUseCase(_Views):
    def execute(self, course_id: int) -> StaffCourseView:
        return self.view(_load(self._courses, course_id))


class AddParticipantsUseCase(_Views):
    def execute(
        self, course_id: int, intra_ids: list[str] | None = None, csv: str = ""
    ) -> AddParticipantsResult:
        course = _load(self._courses, course_id)
        added, existing = course.add_participants(_ids(intra_ids or [], csv))
        self._courses.save(course)
        return AddParticipantsResult(self.view(course), added, existing)


class RequestReviewsUseCase(_Views):
    def __init__(
        self,
        courses: CourseRepository,
        reviews: ReviewRepository,
        events: EventDispatcher,
        today: Today,
    ) -> None:
        super().__init__(courses, reviews)
        self._events = events
        self._today = today

    def execute(
        self, course_id: int, target: ReviewTarget, message: str = ""
    ) -> ReviewRequestResult:
        course = _load(self._courses, course_id)
        if not course.is_open_for_review(self._today()):
            raise ReviewClosed("후기를 받는 중인 과정에만 요청할 수 있습니다")
        reviewed = self._reviews.reviewer_intra_ids_by_course().get(course.id, set())
        recipients = course.review_targets(target, reviewed)
        if recipients:
            self._events.publish(
                ReviewRequested(
                    course_id=course.id,
                    course_name=course.name,
                    intra_ids=tuple(recipients),
                    review_deadline=course.review_deadline,
                    message=message,
                )
            )
        return ReviewRequestResult(course.id, target, recipients)
