import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from library.infrastructure.models import BookReportRow, BookRow, WishRow

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role="student"):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


def make_book(code="B-1", title="클린 코드", **kw):
    defaults = {"category": "컴퓨터/IT", "author": "로버트 마틴", "publisher": "인사이트"}
    return BookRow.objects.create(code=code, title=title, **{**defaults, **kw})


def test_endpoints_require_login():
    anon = APIClient()
    assert anon.get("/api/books/").status_code == 401
    assert anon.post("/api/books/reports", {}, format="json").status_code == 401
    assert anon.post("/api/books/wishes", {}, format="json").status_code == 401


def test_search_by_title_author_isbn_and_category():
    make_book("B-1", "클린 코드", isbn="9788966260959")
    make_book("B-2", "사피엔스", category="인문", author="유발 하라리", publisher="김영사")
    client = login()

    def titles(**params):
        data = client.get("/api/books/", params).json()
        return [b["title"] for b in data["results"]], data

    assert titles(q="클린")[0] == ["클린 코드"]
    assert titles(q="하라리")[0] == ["사피엔스"]
    assert titles(q="9788966")[0] == ["클린 코드"]
    assert titles(category="인문")[0] == ["사피엔스"]
    assert titles(q="코드 마틴")[0] == ["클린 코드"]  # 여러 단어는 AND
    names, data = titles()
    assert len(names) == 2 and data["total"] == 2
    assert sorted(data["categories"]) == ["인문", "컴퓨터/IT"]


def test_book_detail_and_missing():
    book = make_book()
    client = login()
    assert client.get(f"/api/books/{book.pk}").json()["code"] == "B-1"
    res = client.get("/api/books/999999")
    assert res.status_code == 404 and res.json()["code"] == "book_not_found"


def test_student_reports_lost_and_damaged():
    book = make_book()
    client = login()
    res = client.post("/api/books/reports", {"book_id": book.pk, "kind": "lost"}, format="json")
    assert res.status_code == 201
    assert res.json()["status"] == "received" and res.json()["book_title"] == "클린 코드"
    assert "reporter" not in res.json()

    bad = client.post("/api/books/reports", {"book_id": book.pk, "kind": "damaged"}, format="json")
    assert bad.status_code == 400 and bad.json()["code"] == "invalid_report"
    ok = client.post(
        "/api/books/reports",
        {"book_id": book.pk, "kind": "damaged", "detail": "표지 찢어짐"},
        format="json",
    )
    assert ok.status_code == 201
    missing = client.post("/api/books/reports", {"book_id": 999999, "kind": "lost"}, format="json")
    assert missing.status_code == 404
    unknown = client.post("/api/books/reports", {"book_id": book.pk, "kind": "x"}, format="json")
    assert unknown.status_code == 400


def test_wish_and_my_requests_are_private():
    book = make_book()
    student = login()
    student.post("/api/books/reports", {"book_id": book.pk, "kind": "lost"}, format="json")
    res = student.post(
        "/api/books/wishes", {"title": "새 책", "link_url": "https://example.com/b"}, format="json"
    )
    assert res.status_code == 201 and res.json()["status"] == "requested"
    assert (
        student.post(
            "/api/books/wishes", {"title": "x", "link_url": "javascript:1"}, format="json"
        ).status_code
        == 400
    )
    assert student.post("/api/books/wishes", {"title": " "}, format="json").status_code == 400

    mine = student.get("/api/books/my-requests").json()
    assert len(mine["reports"]) == 1 and len(mine["wishes"]) == 1

    staff = login("staff")
    other = staff.get("/api/books/my-requests").json()
    assert other == {"reports": [], "wishes": []}


def test_staff_endpoints_forbid_students():
    student = login()
    for method, url in [
        ("get", "/api/staff/book-reports"),
        ("get", "/api/staff/book-wishes"),
        ("post", "/api/staff/books"),
        ("patch", "/api/staff/books/1"),
        ("post", "/api/staff/book-reports/1/resolve"),
        ("patch", "/api/staff/book-wishes/1"),
    ]:
        assert getattr(student, method)(url, {}, format="json").status_code == 403, url
    assert APIClient().get("/api/staff/book-reports").status_code == 401


def test_staff_handles_reports():
    book = make_book()
    student, staff = login(), login("staff")
    student.post("/api/books/reports", {"book_id": book.pk, "kind": "lost"}, format="json")
    [item] = staff.get("/api/staff/book-reports").json()
    assert item["reporter"]["intra_id"] == "student"
    assert staff.get("/api/staff/book-reports", {"status": "resolved"}).json() == []

    done = staff.post(f"/api/staff/book-reports/{item['id']}/resolve")
    assert done.status_code == 200 and done.json()["status"] == "resolved"
    again = staff.post(f"/api/staff/book-reports/{item['id']}/resolve")
    assert again.status_code == 409 and again.json()["code"] == "invalid_transition"
    assert staff.post("/api/staff/book-reports/999999/resolve").status_code == 404


def test_staff_handles_wishes():
    student, staff = login(), login("staff")
    wish_id = student.post("/api/books/wishes", {"title": "새 책"}, format="json").json()["id"]
    url = f"/api/staff/book-wishes/{wish_id}"

    assert staff.patch(url, {"status": "rejected"}, format="json").status_code == 400
    assert staff.patch(url, {"status": "purchased"}, format="json").status_code == 409
    assert staff.patch(url, {"status": "bogus"}, format="json").status_code == 400
    approved = staff.patch(url, {"status": "approved", "note": "검토 완료"}, format="json")
    assert approved.json()["status"] == "approved" and approved.json()["staff_note"] == "검토 완료"
    assert staff.get("/api/staff/book-wishes", {"status": "approved"}).json()[0]["id"] == wish_id
    assert (
        staff.patch(
            "/api/staff/book-wishes/999999", {"status": "approved"}, format="json"
        ).status_code
        == 404
    )
    assert student.get("/api/books/my-requests").json()["wishes"][0]["status"] == "approved"


def test_staff_creates_and_updates_books():
    staff = login("staff")
    body = {"code": "N-1", "title": "새 책", "category": "인문", "quantity": 2}
    created = staff.post("/api/staff/books", body, format="json")
    assert created.status_code == 201
    book_id = created.json()["id"]
    dup = staff.post("/api/staff/books", body, format="json")
    assert dup.status_code == 409 and dup.json()["code"] == "duplicate_book"

    updated = staff.patch(
        f"/api/staff/books/{book_id}", {"quantity": 0, "code": "IGNORED"}, format="json"
    )
    assert updated.status_code == 200
    assert updated.json()["quantity"] == 0 and updated.json()["code"] == "N-1"
    assert (
        staff.patch(f"/api/staff/books/{book_id}", {"title": " "}, format="json").status_code == 400
    )
    assert staff.patch("/api/staff/books/999999", {"quantity": 1}, format="json").status_code == 404

    located = staff.patch(f"/api/staff/books/{book_id}", {"location": "A-2"}, format="json")
    assert "location" not in located.json()
    assert staff.delete(f"/api/staff/books/{book_id}").status_code == 204
    assert not BookRow.objects.filter(pk=book_id).exists()
    assert staff.delete(f"/api/staff/books/{book_id}").status_code == 404
    assert login().delete(f"/api/staff/books/{book_id}").status_code == 403


def test_import_books_is_idempotent_and_keeps_requests(tmp_path):
    out = StringIO()
    call_command("import_books", stdout=out)
    count = BookRow.objects.count()
    assert count == 518 and "새로 518종" in out.getvalue()

    book = BookRow.objects.first()
    BookReportRow.objects.create(book=book, user=_user(), kind="lost", detail="")
    WishRow.objects.create(user=_user(), title="w")
    book.quantity = 9
    book.save()
    out = StringIO()
    call_command("import_books", stdout=out)
    assert BookRow.objects.count() == count and "새로 0종, 갱신 518종" in out.getvalue()
    assert BookRow.objects.get(pk=book.pk).quantity != 9  # 원본 값으로 복원
    assert BookReportRow.objects.count() == 1 and WishRow.objects.count() == 1


def _user():
    from accounts.infrastructure.models import User

    user, _ = User.objects.get_or_create(
        intra_id="tester", defaults={"name": "t", "role": "student"}
    )
    return user


def test_import_books_custom_file_and_errors(tmp_path):
    good = tmp_path / "b.json"
    good.write_text(json.dumps([{"id": "X-1", "title": "하나", "category": "기타"}]))
    call_command("import_books", file=str(good), stdout=StringIO())
    assert BookRow.objects.get(code="X-1").quantity == 1

    for content in ["not json", json.dumps({"a": 1}), json.dumps([{"id": "", "title": "t"}])]:
        bad = tmp_path / "bad.json"
        bad.write_text(content)
        with pytest.raises(CommandError):
            call_command("import_books", file=str(bad), stdout=StringIO())
    with pytest.raises(CommandError):
        call_command("import_books", file=str(tmp_path / "none.json"), stdout=StringIO())


def test_bundled_data_is_valid():
    from library.application.importer import parse_books

    rows = json.loads((Path(__file__).parents[1] / "data" / "books.json").read_text())
    books = parse_books(rows)
    assert len(books) == 518 and all(
        b.cover_url.startswith("https://") or not b.cover_url for b in books
    )
