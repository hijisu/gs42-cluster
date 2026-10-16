from dataclasses import dataclass
from datetime import date

from common.domain.events import DomainEvent


@dataclass(frozen=True)
class ReviewRequested(DomainEvent):
    """운영팀이 후기 작성을 요청했다. 수신자는 intra ID(아직 가입 전일 수 있음)."""

    course_id: int
    course_name: str
    intra_ids: tuple[str, ...]
    review_deadline: date | None
    message: str = ""
