"""교육과정 집합 루트. 후기 작성 가능 여부는 여기서 판단한다."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from reviews.domain.errors import NotParticipant, ReviewClosed


class CourseStatus(StrEnum):
    UPCOMING = "upcoming"  # 예정
    ONGOING = "ongoing"  # 진행 중
    COMPLETED = "completed"  # 종료(후기를 받는다)


def normalize_intra_id(intra_id: str) -> str:
    return intra_id.strip().lower()


@dataclass
class Course:
    name: str
    start_date: date
    end_date: date
    location: str = ""
    intro: str = ""
    status: CourseStatus = CourseStatus.UPCOMING
    review_deadline: date | None = None
    participants: set[str] = field(default_factory=set)  # 정규화된 intra_id
    id: int | None = None

    def is_participant(self, intra_id: str) -> bool:
        return normalize_intra_id(intra_id) in self.participants

    def is_open_for_review(self, today: date) -> bool:
        """종료된 과정이고 마감일(있다면)이 지나지 않았을 때 후기를 받는다."""
        if self.status != CourseStatus.COMPLETED:
            return False
        return self.review_deadline is None or today <= self.review_deadline

    def can_review(self, intra_id: str, today: date) -> bool:
        return self.is_participant(intra_id) and self.is_open_for_review(today)

    def ensure_can_review(self, intra_id: str, today: date) -> None:
        if not self.is_participant(intra_id):
            raise NotParticipant("참여한 과정에만 후기를 작성할 수 있습니다")
        if not self.is_open_for_review(today):
            raise ReviewClosed("후기를 받지 않는 과정이거나 마감되었습니다")
