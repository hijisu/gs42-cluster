from dataclasses import dataclass
from typing import Protocol

from reviews.domain.course import Course
from reviews.domain.review import Review


@dataclass(frozen=True)
class CourseStats:
    average_rating: float | None
    review_count: int


class CourseRepository(Protocol):
    def list_all(self) -> list[Course]: ...

    def get(self, course_id: int) -> Course | None: ...


class ReviewRepository(Protocol):
    def add(self, review: Review) -> Review:
        """(course, author) 중복이면 AlreadyReviewed를 던진다."""
        ...

    def exists(self, course_id: int, author_id: int) -> bool: ...

    def list_for_course(self, course_id: int) -> list[Review]: ...

    def reviewed_course_ids(self, author_id: int) -> set[int]: ...

    def stats_by_course(self) -> dict[int, CourseStats]: ...
