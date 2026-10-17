from dataclasses import dataclass
from enum import Enum

from library.domain.errors import InvalidReport, InvalidTransition


class ReportKind(str, Enum):
    LOST = "lost"
    DAMAGED = "damaged"


class ReportStatus(str, Enum):
    RECEIVED = "received"
    RESOLVED = "resolved"


@dataclass
class BookReport:
    book_id: int
    user_id: int
    kind: ReportKind
    detail: str = ""
    status: ReportStatus = ReportStatus.RECEIVED
    id: int | None = None

    def __post_init__(self) -> None:
        self.detail = self.detail.strip()
        if self.kind == ReportKind.DAMAGED and not self.detail:
            raise InvalidReport("훼손 신고에는 훼손 내용이 필요합니다")

    def resolve(self) -> None:
        if self.status == ReportStatus.RESOLVED:
            raise InvalidTransition("이미 처리된 신고입니다")
        self.status = ReportStatus.RESOLVED
