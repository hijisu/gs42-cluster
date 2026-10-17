from dataclasses import dataclass

from library.application.importer import parse_books
from library.application.ports import (
    BookRepository,
    ReportRepository,
    ReportView,
    WishRepository,
    WishView,
)
from library.domain.book import Book
from library.domain.errors import (
    BookNotFound,
    DuplicateBook,
    ReportNotFound,
    WishNotFound,
)
from library.domain.report import BookReport, ReportKind
from library.domain.wish import Wish, WishStatus

MAX_RESULTS = 200


@dataclass(frozen=True)
class SearchResult:
    books: list[Book]
    total: int
    categories: list[str]


class SearchBooksUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, query: str = "", category: str = "") -> SearchResult:
        found = self._books.search(query.strip(), category.strip())
        return SearchResult(
            books=found[:MAX_RESULTS], total=len(found), categories=self._books.categories()
        )


class GetBookUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, book_id: int) -> Book:
        book = self._books.get(book_id)
        if book is None:
            raise BookNotFound("도서를 찾을 수 없습니다")
        return book


class CreateReportUseCase:
    def __init__(self, books: BookRepository, reports: ReportRepository) -> None:
        self._books = books
        self._reports = reports

    def execute(self, user_id: int, book_id: int, kind: str, detail: str) -> ReportView:
        if self._books.get(book_id) is None:
            raise BookNotFound("도서를 찾을 수 없습니다")
        report = self._reports.add(
            BookReport(book_id=book_id, user_id=user_id, kind=ReportKind(kind), detail=detail)
        )
        return self._reports.view(report.id)


class CreateWishUseCase:
    def __init__(self, wishes: WishRepository) -> None:
        self._wishes = wishes

    def execute(
        self, user_id: int, title: str, author: str = "", reason: str = "", link_url: str = ""
    ) -> WishView:
        wish = self._wishes.add(
            Wish(user_id=user_id, title=title, author=author, reason=reason, link_url=link_url)
        )
        return self._wishes.view(wish.id)


class ListMyLibraryRequestsUseCase:
    def __init__(self, reports: ReportRepository, wishes: WishRepository) -> None:
        self._reports = reports
        self._wishes = wishes

    def execute(self, user_id: int) -> tuple[list[ReportView], list[WishView]]:
        return self._reports.list_for_user(user_id), self._wishes.list_for_user(user_id)


class ListReportsUseCase:
    def __init__(self, reports: ReportRepository) -> None:
        self._reports = reports

    def execute(self, status: str | None = None) -> list[ReportView]:
        return self._reports.list_all(status)


class ResolveReportUseCase:
    def __init__(self, reports: ReportRepository) -> None:
        self._reports = reports

    def execute(self, report_id: int) -> ReportView:
        report = self._reports.get(report_id)
        if report is None:
            raise ReportNotFound("신고를 찾을 수 없습니다")
        report.resolve()
        self._reports.save(report)
        return self._reports.view(report_id)


class ListWishesUseCase:
    def __init__(self, wishes: WishRepository) -> None:
        self._wishes = wishes

    def execute(self, status: str | None = None) -> list[WishView]:
        return self._wishes.list_all(status)


class UpdateWishUseCase:
    def __init__(self, wishes: WishRepository) -> None:
        self._wishes = wishes

    def execute(self, wish_id: int, status: str, note: str = "") -> WishView:
        wish = self._wishes.get(wish_id)
        if wish is None:
            raise WishNotFound("희망 도서 신청을 찾을 수 없습니다")
        wish.move_to(WishStatus(status), note)
        self._wishes.save(wish)
        return self._wishes.view(wish_id)


class CreateBookUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, book: Book) -> Book:
        if self._books.get_by_code(book.code) is not None:
            raise DuplicateBook("이미 있는 도서 코드입니다")
        return self._books.add(book)


class UpdateBookUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, book_id: int, changes: dict) -> Book:
        book = self._books.get(book_id)
        if book is None:
            raise BookNotFound("도서를 찾을 수 없습니다")
        # 도메인 검증을 다시 거치도록 새 객체로 만든다.
        data = {**book.__dict__, **changes}
        updated = Book(**data)
        self._books.save(updated)
        return updated


class DeleteBookUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, book_id: int) -> None:
        if not self._books.delete(book_id):
            raise BookNotFound("도서를 찾을 수 없습니다")


class ImportBooksUseCase:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    def execute(self, rows: list[dict]) -> tuple[int, int]:
        return self._books.upsert_many(parse_books(rows))
