"""교육과정 집합 루트. 후기 작성 가능 여부는 여기서 판단한다."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from reviews.domain.errors import InvalidCourse, NotParticipant, ReviewClosed


class CourseStatus(StrEnum):
    UPCOMING = "upcoming"  # 예정
    ONGOING = "ongoing"  # 진행 중
    COMPLETED = "completed"  # 종료(후기를 받는다)


class ReviewTarget(StrEnum):
    ALL = "all"  # 참여자 전체
    PENDING = "pending"  # 아직 후기를 쓰지 않은 참여자


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

    def __post_init__(self) -> None:
        # 저장된 데이터를 읽을 때 실패하지 않도록 검증은 validate()/update()에서만 한다.
        self.participants = {normalize_intra_id(p) for p in self.participants}

    def validate(self) -> None:
        if not self.name.strip():
            raise InvalidCourse("과정명을 입력해 주세요")
        if self.end_date < self.start_date:
            raise InvalidCourse("종료일은 시작일 이후여야 합니다")
        if self.review_deadline is not None and self.review_deadline < self.end_date:
            raise InvalidCourse("후기 마감일은 종료일 이후여야 합니다")

    def update(self, **changes) -> None:
        """일부 필드를 바꾼다. 불변식을 어기면 변경을 되돌리고 오류를 던진다."""
        allowed = {
            "name",
            "start_date",
            "end_date",
            "location",
            "intro",
            "status",
            "review_deadline",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise InvalidCourse(f"수정할 수 없는 필드입니다: {', '.join(sorted(unknown))}")
        before = {k: getattr(self, k) for k in changes}
        for key, value in changes.items():
            setattr(self, key, value)
        try:
            self.validate()
        except InvalidCourse:
            for key, value in before.items():
                setattr(self, key, value)
            raise

    def add_participants(self, intra_ids: list[str]) -> tuple[list[str], list[str]]:
        """(새로 추가된 ID, 이미 있던 ID)를 돌려준다."""
        added, existing = [], []
        for raw in intra_ids:
            intra_id = normalize_intra_id(raw)
            if intra_id in self.participants:
                existing.append(intra_id)
            else:
                self.participants.add(intra_id)
                added.append(intra_id)
        return added, existing

    def review_targets(self, target: ReviewTarget, reviewed: set[str]) -> list[str]:
        """후기 요청을 보낼 참여자(정렬). pending이면 이미 쓴 사람은 제외한다."""
        if target == ReviewTarget.ALL:
            return sorted(self.participants)
        return sorted(self.participants - {normalize_intra_id(r) for r in reviewed})
