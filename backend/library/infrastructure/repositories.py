from django.db import transaction
from django.db.models import Q

from library.application.ports import ReportView, WishView
from library.domain.book import Book
from library.domain.report import BookReport, ReportKind, ReportStatus
from library.domain.wish import Wish, WishStatus
from library.infrastructure.models import BookReportRow, BookRow, WishRow

_BOOK_FIELDS = (
    "title",
    "author",
    "publisher",
    "isbn",
    "category",
    "quantity",
    "description",
    "cover_url",
    "link_url",
    "pub_date",
    "location",
)


def _book(row: BookRow) -> Book:
    return Book(
        id=row.pk,
        code=row.code,
        **{f: getattr(row, f) for f in _BOOK_FIELDS},
    )


def _values(book: Book) -> dict:
    return {f: getattr(book, f) for f in _BOOK_FIELDS}


class DjangoBookRepository:
    def search(self, query: str, category: str) -> list[Book]:
        rows = BookRow.objects.all()
        if category:
            rows = rows.filter(category=category)
        for term in query.split():
            rows = rows.filter(
                Q(title__icontains=term)
                | Q(author__icontains=term)
                | Q(publisher__icontains=term)
                | Q(isbn__icontains=term)
                | Q(code__icontains=term)
            )
        return [_book(r) for r in rows]

    def categories(self) -> list[str]:
        return list(
            BookRow.objects.order_by("category").values_list("category", flat=True).distinct()
        )

    def get(self, book_id: int) -> Book | None:
        row = BookRow.objects.filter(pk=book_id).first()
        return _book(row) if row else None

    def get_by_code(self, code: str) -> Book | None:
        row = BookRow.objects.filter(code=code).first()
        return _book(row) if row else None

    def add(self, book: Book) -> Book:
        book.id = BookRow.objects.create(code=book.code, **_values(book)).pk
        return book

    def save(self, book: Book) -> None:
        BookRow.objects.filter(pk=book.id).update(**_values(book))

    def delete(self, book_id: int) -> bool:
        deleted, _ = BookRow.objects.filter(pk=book_id).delete()
        return bool(deleted)

    @transaction.atomic
    def upsert_many(self, books: list[Book]) -> tuple[int, int]:
        created = updated = 0
        for book in books:
            _, was_created = BookRow.objects.update_or_create(
                code=book.code, defaults=_values(book)
            )
            created += was_created
            updated += not was_created
        return created, updated


def _report(row: BookReportRow) -> BookReport:
    return BookReport(
        id=row.pk,
        book_id=row.book_id,
        user_id=row.user_id,
        kind=ReportKind(row.kind),
        detail=row.detail,
        status=ReportStatus(row.status),
    )


def _report_view(row: BookReportRow) -> ReportView:
    return ReportView(
        report=_report(row),
        book_code=row.book.code,
        book_title=row.book.title,
        reporter_intra_id=row.user.intra_id,
        reporter_name=row.user.name,
        created_at=row.created_at,
    )


class DjangoReportRepository:
    _qs = BookReportRow.objects.select_related("book", "user")

    def add(self, report: BookReport) -> BookReport:
        report.id = BookReportRow.objects.create(
            book_id=report.book_id,
            user_id=report.user_id,
            kind=report.kind.value,
            detail=report.detail,
            status=report.status.value,
        ).pk
        return report

    def get(self, report_id: int) -> BookReport | None:
        row = BookReportRow.objects.filter(pk=report_id).first()
        return _report(row) if row else None

    def save(self, report: BookReport) -> None:
        BookReportRow.objects.filter(pk=report.id).update(status=report.status.value)

    def view(self, report_id: int) -> ReportView:
        return _report_view(self._qs.get(pk=report_id))

    def list_for_user(self, user_id: int) -> list[ReportView]:
        return [_report_view(r) for r in self._qs.filter(user_id=user_id)]

    def list_all(self, status: str | None) -> list[ReportView]:
        rows = self._qs.filter(status=status) if status else self._qs.all()
        return [_report_view(r) for r in rows]


def _wish(row: WishRow) -> Wish:
    return Wish(
        id=row.pk,
        user_id=row.user_id,
        title=row.title,
        author=row.author,
        reason=row.reason,
        link_url=row.link_url,
        status=WishStatus(row.status),
        staff_note=row.staff_note,
    )


def _wish_view(row: WishRow) -> WishView:
    return WishView(
        wish=_wish(row),
        requester_intra_id=row.user.intra_id,
        requester_name=row.user.name,
        created_at=row.created_at,
    )


class DjangoWishRepository:
    _qs = WishRow.objects.select_related("user")

    def add(self, wish: Wish) -> Wish:
        wish.id = WishRow.objects.create(
            user_id=wish.user_id,
            title=wish.title,
            author=wish.author,
            reason=wish.reason,
            link_url=wish.link_url,
            status=wish.status.value,
        ).pk
        return wish

    def get(self, wish_id: int) -> Wish | None:
        row = WishRow.objects.filter(pk=wish_id).first()
        return _wish(row) if row else None

    def save(self, wish: Wish) -> None:
        WishRow.objects.filter(pk=wish.id).update(
            status=wish.status.value, staff_note=wish.staff_note
        )

    def view(self, wish_id: int) -> WishView:
        return _wish_view(self._qs.get(pk=wish_id))

    def list_for_user(self, user_id: int) -> list[WishView]:
        return [_wish_view(r) for r in self._qs.filter(user_id=user_id)]

    def list_all(self, status: str | None) -> list[WishView]:
        rows = self._qs.filter(status=status) if status else self._qs.all()
        return [_wish_view(r) for r in rows]
