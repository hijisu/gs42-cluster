"""42gslib 도서 JSON을 Book 도메인 객체로 변환한다(프레임워크 없음)."""

import html

from library.domain.book import Book
from library.domain.errors import InvalidBook

SOURCE_ORIGIN = "https://42gslib.pages.dev"


def _text(raw: dict, key: str) -> str:
    return html.unescape(str(raw.get(key) or "")).strip()


def _cover(path: str) -> str:
    if not path:
        return ""
    if path.startswith("/"):
        return SOURCE_ORIGIN + path
    return path if path.startswith("https://") else ""


def _link(url: str) -> str:
    return url if url.startswith("https://") else ""


def parse_books(rows: list[dict]) -> list[Book]:
    books, seen = [], set()
    for index, raw in enumerate(rows):
        try:
            book = Book(
                code=_text(raw, "id"),
                title=_text(raw, "title"),
                category=_text(raw, "category") or "기타",
                quantity=int(raw.get("quantity") or 1),
                author=_text(raw, "author"),
                publisher=_text(raw, "publisher"),
                isbn=_text(raw, "isbn"),
                description=_text(raw, "description"),
                cover_url=_cover(_text(raw, "coverUrl")),
                link_url=_link(_text(raw, "aladinLink")),
                pub_date=_text(raw, "pubDate"),
            )
        except (InvalidBook, TypeError, ValueError) as exc:
            raise InvalidBook(f"{index + 1}번째 도서가 올바르지 않습니다: {exc}") from exc
        if book.code in seen:
            raise InvalidBook(f"도서 코드가 중복되었습니다: {book.code}")
        seen.add(book.code)
        books.append(book)
    return books
