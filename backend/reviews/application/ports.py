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

    def add(self, course: Course) -> Course: ...

    def save(self, course: Course) -> None:
        """과정 필드를 저장하고 새 참여자를 추가한다(참여자 제거는 지원하지 않는다)."""
        ...

    def get(self, course_id: int) -> Course | None: ...


class ReviewRepository(Protocol):
    def add(self, review: Review) -> Review:
        """(course, author) 중복이면 AlreadyReviewed를 던진다."""
        ...

    def exists(self, course_id: int, author_id: int) -> bool: ...

    def get(self, review_id: int) -> Review | None: ...

    def save(self, review: Review) -> None:
        """만족도·내용·태그·익명 여부를 저장한다(작성자·과정·작성 시각은 바뀌지 않는다)."""
        ...

    def list_for_course(self, course_id: int) -> list[Review]: ...

    def reviewed_course_ids(self, author_id: int) -> set[int]: ...

    def stats_by_course(self) -> dict[int, CourseStats]: ...

    def reviewer_intra_ids_by_course(self) -> dict[int, set[str]]:
        """과정별로 후기를 쓴 사용자의 intra_id(소문자)."""
        ...
