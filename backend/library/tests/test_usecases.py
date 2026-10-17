"""유스케이스 테스트: DB 없이 인메모리 가짜 저장소로 실행한다."""

from datetime import UTC, datetime

import pytest

from library.application import usecases as uc
from library.application.ports import ReportView, WishView
from library.domain.book import Book
from library.domain.errors import (
    BookNotFound,
    DuplicateBook,
    InvalidBook,
    InvalidReport,
    InvalidTransition,
    ReportNotFound,
    WishNotFound,
)
from library.domain.report import ReportKind
from library.domain.wish import WishStatus

NOW = datetime(2026, 10, 17, tzinfo=UTC)


class FakeBooks:
    def __init__(self, books=(), lost=None):
        self.rows = {}
        self.lost = lost or {}  # book_id → 접수된 분실 신고 수
        for b in books:
            self.add(b)

    def lost_counts(self, book_ids):
        return {i: self.lost[i] for i in book_ids if self.lost.get(i)}

    def search(self, query, category):
        terms = query.split()
        return [
            b
            for b in self.rows.values()
            if (not category or b.category == category)
            and all(t in f"{b.title} {b.author} {b.publisher} {b.isbn}" for t in terms)
        ]

    def categories(self):
        return sorted({b.category for b in self.rows.values()})

    def get(self, book_id):
        return self.rows.get(book_id)

    def get_by_code(self, code):
        return next((b for b in self.rows.values() if b.code == code), None)

    def add(self, book):
        book.id = len(self.rows) + 1
        self.rows[book.id] = book
        return book

    def save(self, book):
        self.rows[book.id] = book

    def delete(self, book_id):
        return self.rows.pop(book_id, None) is not None

    def upsert_many(self, books):
        created = updated = 0
        for b in books:
            existing = self.get_by_code(b.code)
            if existing:
                b.id = existing.id
                self.rows[b.id] = b
                updated += 1
            else:
                self.add(b)
                created += 1
        return created, updated


class FakeReports:
    def __init__(self, books):
        self._books = books
        self.rows = {}

    def add(self, report):
        report.id = len(self.rows) + 1
        self.rows[report.id] = report
        return report

    def get(self, report_id):
        return self.rows.get(report_id)

    def save(self, report):
        self.rows[report.id] = report

    def view(self, report_id):
        r = self.rows[report_id]
        book = self._books.get(r.book_id)
        return ReportView(r, book.code, book.title, f"user{r.user_id}", "이름", NOW)

    def list_for_user(self, user_id):
        return [self.view(i) for i, r in self.rows.items() if r.user_id == user_id]

    def list_all(self, status):
        return [
            self.view(i) for i, r in self.rows.items() if not status or r.status.value == status
        ]


class FakeWishes:
    def __init__(self):
        self.rows = {}

    def add(self, wish):
        wish.id = len(self.rows) + 1
        self.rows[wish.id] = wish
        return wish

    def get(self, wish_id):
        return self.rows.get(wish_id)

    def save(self, wish):
        self.rows[wish.id] = wish

    def view(self, wish_id):
        w = self.rows[wish_id]
        return WishView(w, f"user{w.user_id}", "이름", NOW)

    def list_for_user(self, user_id):
        return [self.view(i) for i, w in self.rows.items() if w.user_id == user_id]

    def list_all(self, status):
        return [
            self.view(i) for i, w in self.rows.items() if not status or w.status.value == status
        ]


def book(code="B-1", title="클린 코드", **kw):
    return Book(code=code, title=title, category=kw.pop("category", "컴퓨터/IT"), **kw)


def test_search_limits_results_but_reports_total_and_categories():
    books = FakeBooks(book(f"B-{i}", f"책 {i}") for i in range(uc.MAX_RESULTS + 5))
    books.add(book("H-1", "사피엔스", category="인문"))
    result = uc.SearchBooksUseCase(books).execute("  ")
    assert len(result.books) == uc.MAX_RESULTS
    assert result.total == uc.MAX_RESULTS + 6
    assert result.categories == ["인문", "컴퓨터/IT"]


def test_search_filters_by_terms_and_category():
    books = FakeBooks([book(author="마틴"), book("H-1", "사피엔스", category="인문")])
    search = uc.SearchBooksUseCase(books)
    assert [v.book.code for v in search.execute("클린 마틴").books] == ["B-1"]
    assert [v.book.code for v in search.execute("", "인문").books] == ["H-1"]
    assert search.execute("없는책").total == 0


def test_get_book_missing_raises():
    with pytest.raises(BookNotFound):
        uc.GetBookUseCase(FakeBooks()).execute(1)


def test_report_unknown_book_is_not_found_and_damaged_needs_detail():
    books = FakeBooks([book()])
    create = uc.CreateReportUseCase(books, FakeReports(books))
    with pytest.raises(BookNotFound):
        create.execute(1, 99, "lost", "")
    with pytest.raises(InvalidReport):
        create.execute(1, 1, "damaged", "")
    view = create.execute(1, 1, "lost", "서가에 없음")
    assert view.report.kind == ReportKind.LOST and view.book_title == "클린 코드"


def test_my_requests_only_include_own_items():
    books, wishes = FakeBooks([book()]), FakeWishes()
    reports = FakeReports(books)
    uc.CreateReportUseCase(books, reports).execute(1, 1, "lost", "")
    uc.CreateReportUseCase(books, reports).execute(2, 1, "lost", "")
    uc.CreateWishUseCase(wishes).execute(1, "새 책")
    mine_reports, mine_wishes = uc.ListMyLibraryRequestsUseCase(reports, wishes).execute(1)
    assert len(mine_reports) == 1 and len(mine_wishes) == 1
    assert uc.ListMyLibraryRequestsUseCase(reports, wishes).execute(3) == ([], [])


def test_resolve_report_once_and_missing():
    books = FakeBooks([book()])
    reports = FakeReports(books)
    uc.CreateReportUseCase(books, reports).execute(1, 1, "lost", "")
    resolve = uc.ResolveReportUseCase(reports)
    assert resolve.execute(1).report.status.value == "resolved"
    assert uc.ListReportsUseCase(reports).execute("received") == []
    with pytest.raises(InvalidTransition):
        resolve.execute(1)
    with pytest.raises(ReportNotFound):
        resolve.execute(99)


def test_update_wish_follows_state_machine():
    wishes = FakeWishes()
    uc.CreateWishUseCase(wishes).execute(1, "새 책", link_url="https://example.com")
    update = uc.UpdateWishUseCase(wishes)
    assert update.execute(1, "approved").wish.status == WishStatus.APPROVED
    assert update.execute(1, "purchased", "주문").wish.staff_note == "주문"
    with pytest.raises(InvalidTransition):
        update.execute(1, "approved")
    with pytest.raises(WishNotFound):
        update.execute(99, "approved")
    assert uc.ListWishesUseCase(wishes).execute("purchased")[0].wish.id == 1


def test_create_book_rejects_duplicate_code_and_update_revalidates():
    books = FakeBooks()
    created = uc.CreateBookUseCase(books).execute(book())
    with pytest.raises(DuplicateBook):
        uc.CreateBookUseCase(books).execute(book(title="다른 제목"))
    update = uc.UpdateBookUseCase(books)
    assert update.execute(created.id, {"quantity": 3}).quantity == 3
    with pytest.raises(InvalidBook):
        update.execute(created.id, {"title": " "})
    assert books.get(created.id).title == "클린 코드"
    with pytest.raises(BookNotFound):
        update.execute(99, {"quantity": 1})


def test_delete_book_and_import_counts():
    books = FakeBooks()
    importer = uc.ImportBooksUseCase(books)
    rows = [{"id": "X-1", "title": "하나", "category": "기타"}]
    assert importer.execute(rows) == (1, 0)
    assert importer.execute(rows) == (0, 1)
    uc.DeleteBookUseCase(books).execute(1)
    with pytest.raises(BookNotFound):
        uc.DeleteBookUseCase(books).execute(1)


def test_search_and_get_expose_lost_count_and_derived_availability():
    books = FakeBooks(
        [book("A-1", "책 A", quantity=3), book("B-1", "책 B", quantity=1)], lost={1: 1, 2: 5}
    )
    found = uc.SearchBooksUseCase(books).execute()
    by_code = {v.book.code: v for v in found.books}
    assert (by_code["A-1"].lost_count, by_code["A-1"].available_quantity) == (1, 2)
    # 분실 신고가 수량을 넘어도 비치 수는 0 미만이 되지 않는다. 수량 자체는 그대로다.
    assert (by_code["B-1"].lost_count, by_code["B-1"].available_quantity) == (5, 0)
    assert books.rows[1].quantity == 3
    one = uc.GetBookUseCase(books).execute(1)
    assert one.lost_count == 1 and one.available_quantity == 2
    assert uc.GetBookUseCase(FakeBooks([book()])).execute(1).available_quantity == 1
