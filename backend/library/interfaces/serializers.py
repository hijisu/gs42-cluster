from rest_framework import serializers

from library.application.ports import ReportView, WishView
from library.domain.book import Book
from library.domain.report import ReportKind
from library.domain.wish import WishStatus


class ReportSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=[k.value for k in ReportKind])
    detail = serializers.CharField(allow_blank=True, max_length=2000, default="")


class WishSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    author = serializers.CharField(allow_blank=True, max_length=300, default="")
    reason = serializers.CharField(allow_blank=True, max_length=2000, default="")
    link_url = serializers.URLField(allow_blank=True, max_length=500, default="")


class WishStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s.value for s in WishStatus])
    note = serializers.CharField(allow_blank=True, max_length=2000, default="")


class BookWriteSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    title = serializers.CharField(max_length=300)
    category = serializers.CharField(max_length=40)
    quantity = serializers.IntegerField(min_value=0, max_value=1000, default=1)
    author = serializers.CharField(allow_blank=True, max_length=300, default="")
    publisher = serializers.CharField(allow_blank=True, max_length=200, default="")
    isbn = serializers.CharField(allow_blank=True, max_length=20, default="")
    description = serializers.CharField(allow_blank=True, max_length=5000, default="")
    cover_url = serializers.URLField(allow_blank=True, max_length=500, default="")
    link_url = serializers.URLField(allow_blank=True, max_length=500, default="")
    pub_date = serializers.CharField(allow_blank=True, max_length=20, default="")


def book_payload(b: Book) -> dict:
    return {
        "id": b.id,
        "code": b.code,
        "title": b.title,
        "author": b.author,
        "publisher": b.publisher,
        "isbn": b.isbn,
        "category": b.category,
        "quantity": b.quantity,
        "description": b.description,
        "cover_url": b.cover_url,
        "link_url": b.link_url,
        "pub_date": b.pub_date,
    }


def report_payload(v: ReportView, staff: bool = False) -> dict:
    r = v.report
    data = {
        "id": r.id,
        "book_id": r.book_id,
        "book_code": v.book_code,
        "book_title": v.book_title,
        "kind": r.kind.value,
        "detail": r.detail,
        "status": r.status.value,
        "created_at": v.created_at,
    }
    if staff:
        data["reporter"] = {"intra_id": v.reporter_intra_id, "name": v.reporter_name}
    return data


def wish_payload(v: WishView, staff: bool = False) -> dict:
    w = v.wish
    data = {
        "id": w.id,
        "title": w.title,
        "author": w.author,
        "reason": w.reason,
        "link_url": w.link_url,
        "status": w.status.value,
        "staff_note": w.staff_note,
        "created_at": v.created_at,
    }
    if staff:
        data["requester"] = {"intra_id": v.requester_intra_id, "name": v.requester_name}
    return data


class BookPageSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
