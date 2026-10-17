from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from library.domain.book import Book
from library.domain.report import BookReport
from library.domain.wish import Wish


@dataclass(frozen=True)
class ReportView:
    report: BookReport
    book_code: str
    book_title: str
    reporter_intra_id: str
    reporter_name: str
    created_at: datetime


@dataclass(frozen=True)
class WishView:
    wish: Wish
    requester_intra_id: str
    requester_name: str
    created_at: datetime


@dataclass(frozen=True)
class BookView:
    """도서 + 접수된 분실 신고 수. 비치 수는 그로부터 계산한 파생값이다."""

    book: Book
    lost_count: int = 0

    @property
    def available_quantity(self) -> int:
        return self.book.available_quantity(self.lost_count)


class BookRepository(Protocol):
    def lost_counts(self, book_ids: list[int]) -> dict[int, int]:
        """book_id → 접수(미처리)된 분실 신고 수. 훼손 신고와 처리 완료 신고는 세지 않는다."""
        ...

    def search(self, query: str, category: str) -> list[Book]: ...
    def categories(self) -> list[str]: ...
    def get(self, book_id: int) -> Book | None: ...
    def get_by_code(self, code: str) -> Book | None: ...
    def add(self, book: Book) -> Book: ...
    def save(self, book: Book) -> None: ...
    def delete(self, book_id: int) -> bool: ...
    def upsert_many(self, books: list[Book]) -> tuple[int, int]:
        """(생성 건수, 갱신 건수)"""
        ...


class ReportRepository(Protocol):
    def add(self, report: BookReport) -> BookReport: ...
    def get(self, report_id: int) -> BookReport | None: ...
    def save(self, report: BookReport) -> None: ...
    def view(self, report_id: int) -> ReportView: ...
    def list_for_user(self, user_id: int) -> list[ReportView]: ...
    def list_all(self, status: str | None) -> list[ReportView]: ...


class WishRepository(Protocol):
    def add(self, wish: Wish) -> Wish: ...
    def get(self, wish_id: int) -> Wish | None: ...
    def save(self, wish: Wish) -> None: ...
    def view(self, wish_id: int) -> WishView: ...
    def list_for_user(self, user_id: int) -> list[WishView]: ...
    def list_all(self, status: str | None) -> list[WishView]: ...
