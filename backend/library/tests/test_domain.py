import pytest

from library.application.importer import parse_books
from library.domain.book import Book
from library.domain.errors import InvalidBook, InvalidReport, InvalidTransition, InvalidWish
from library.domain.report import BookReport, ReportKind, ReportStatus
from library.domain.wish import Wish, WishStatus


def test_book_requires_code_title_and_non_negative_quantity():
    with pytest.raises(InvalidBook):
        Book(code=" ", title="t", category="c")
    with pytest.raises(InvalidBook):
        Book(code="A", title=" ", category="c")
    with pytest.raises(InvalidBook):
        Book(code="A", title="t", category="c", quantity=-1)


def test_damaged_report_needs_detail_but_lost_does_not():
    BookReport(book_id=1, user_id=1, kind=ReportKind.LOST)
    with pytest.raises(InvalidReport):
        BookReport(book_id=1, user_id=1, kind=ReportKind.DAMAGED, detail="  ")


def test_report_resolves_once():
    report = BookReport(book_id=1, user_id=1, kind=ReportKind.LOST)
    report.resolve()
    assert report.status == ReportStatus.RESOLVED
    with pytest.raises(InvalidTransition):
        report.resolve()


def test_wish_transitions():
    wish = Wish(user_id=1, title="새 책")
    wish.move_to(WishStatus.APPROVED)
    wish.move_to(WishStatus.PURCHASED, "주문함")
    assert wish.staff_note == "주문함"
    with pytest.raises(InvalidTransition):
        wish.move_to(WishStatus.REJECTED, "사유")


def test_wish_cannot_skip_approval_and_rejection_needs_reason():
    wish = Wish(user_id=1, title="새 책")
    with pytest.raises(InvalidTransition):
        wish.move_to(WishStatus.PURCHASED)
    with pytest.raises(InvalidWish):
        wish.move_to(WishStatus.REJECTED)
    wish.move_to(WishStatus.REJECTED, "중복 도서")
    assert wish.status == WishStatus.REJECTED
    with pytest.raises(InvalidTransition):
        wish.move_to(WishStatus.APPROVED)
    with pytest.raises(InvalidWish):
        Wish(user_id=1, title=" ")


def row(**kw):
    return {"id": "GSIA-IT-001", "title": "책", "quantity": 2, "category": "컴퓨터/IT", **kw}


def test_parse_books_normalizes_source_fields():
    [book] = parse_books(
        [
            row(
                coverUrl="/covers/GSIA-IT-001.jpg",
                aladinLink="https://www.aladin.co.kr/x?a=1&amp;b=2",
                author="저자 (지은이)",
            )
        ]
    )
    assert book.cover_url == "https://42gslib.pages.dev/covers/GSIA-IT-001.jpg"
    assert book.link_url == "https://www.aladin.co.kr/x?a=1&b=2"
    assert book.quantity == 2


def test_parse_books_drops_unsafe_urls_and_rejects_bad_rows():
    [book] = parse_books([row(coverUrl="javascript:alert(1)", aladinLink="http://insecure")])
    assert book.cover_url == "" and book.link_url == ""
    assert parse_books([row(category="")])[0].category == "기타"
    with pytest.raises(InvalidBook):
        parse_books([row(), row()])
    with pytest.raises(InvalidBook):
        parse_books([row(title="")])
    with pytest.raises(InvalidBook):
        parse_books([row(quantity="많음")])
