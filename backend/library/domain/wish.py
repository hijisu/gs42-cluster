from dataclasses import dataclass
from enum import Enum

from library.domain.errors import InvalidTransition, InvalidWish


class WishStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PURCHASED = "purchased"


_NEXT = {
    WishStatus.REQUESTED: {WishStatus.APPROVED, WishStatus.REJECTED},
    WishStatus.APPROVED: {WishStatus.PURCHASED, WishStatus.REJECTED},
    WishStatus.REJECTED: set(),
    WishStatus.PURCHASED: set(),
}


@dataclass
class Wish:
    user_id: int
    title: str
    author: str = ""
    reason: str = ""
    link_url: str = ""
    status: WishStatus = WishStatus.REQUESTED
    staff_note: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise InvalidWish("희망 도서 제목이 필요합니다")

    def move_to(self, status: WishStatus, note: str = "") -> None:
        if status not in _NEXT[self.status]:
            raise InvalidTransition(f"{self.status.value}에서 {status.value}로 바꿀 수 없습니다")
        if status == WishStatus.REJECTED and not note.strip():
            raise InvalidWish("반려 사유가 필요합니다")
        self.status = status
        if note.strip():
            self.staff_note = note.strip()
