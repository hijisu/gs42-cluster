"""교육과정 집합 루트. 후기 작성 가능 여부는 여기서 판단한다."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from reviews.domain.errors import InvalidCourse, NotParticipant, ReviewClosed


class CourseStatus(StrEnum):
    """날짜로 계산하는 진행 단계(저장하지 않는다). 상태는 직접 바꾸지 않는다."""

    UPCOMING = "upcoming"  # 시작 전
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
    review_deadline: date | None = None
    participants: set[str] = field(default_factory=set)  # 정규화된 intra_id
    id: int | None = None

    def is_participant(self, intra_id: str) -> bool:
        return normalize_intra_id(intra_id) in self.participants

    def phase(self, today: date) -> CourseStatus:
        if today < self.start_date:
            return CourseStatus.UPCOMING
        if today < self.end_date:
            return CourseStatus.ONGOING
        return CourseStatus.COMPLETED

    def is_open_for_review(self, today: date) -> bool:
        """종료일이 되었고 마감일(있다면)이 지나지 않았을 때 후기를 받는다."""
        if self.phase(today) != CourseStatus.COMPLETED:
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

    def remove_participants(self, intra_ids: list[str]) -> tuple[list[str], list[str]]:
        """(제거된 ID, 참여자가 아니던 ID). 이미 쓴 후기는 남고 작성률에서만 빠진다."""
        removed, missing = [], []
        for raw in intra_ids:
            intra_id = normalize_intra_id(raw)
            if intra_id in self.participants:
                self.participants.discard(intra_id)
                removed.append(intra_id)
            else:
                missing.append(intra_id)
        return removed, missing

    def review_targets(self, target: ReviewTarget, reviewed: set[str]) -> list[str]:
        """후기 요청을 보낼 참여자(정렬). pending이면 이미 쓴 사람은 제외한다."""
        if target == ReviewTarget.ALL:
            return sorted(self.participants)
        return sorted(self.participants - {normalize_intra_id(r) for r in reviewed})
