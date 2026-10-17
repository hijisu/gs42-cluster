"""운영팀 전용 도서 API. 모든 뷰에 IsStaff를 적용한다."""

from rest_framework import status
from rest_framework.response import Response

from accounts.interfaces.decorators import staff_api
from library.domain.book import Book
from library.interfaces import deps
from library.interfaces.serializers import (
    BookWriteSerializer,
    WishStatusSerializer,
    book_payload,
    report_payload,
    wish_payload,
)


@staff_api(["POST"])
def create_book(request):
    body = BookWriteSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    book = deps.create_book().execute(Book(**body.validated_data))
    return Response(book_payload(book), status=status.HTTP_201_CREATED)


@staff_api(["PATCH"])
def update_book(request, book_id: int):
    body = BookWriteSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    changes = {k: v for k, v in body.validated_data.items() if k != "code"}
    return Response(book_payload(deps.update_book().execute(book_id, changes)))


@staff_api(["GET"])
def reports(request):
    items = deps.list_reports().execute(request.query_params.get("status") or None)
    return Response([report_payload(v, staff=True) for v in items])


@staff_api(["POST"])
def resolve_report(request, report_id: int):
    return Response(report_payload(deps.resolve_report().execute(report_id), staff=True))


@staff_api(["GET"])
def wishes(request):
    items = deps.list_wishes().execute(request.query_params.get("status") or None)
    return Response([wish_payload(v, staff=True) for v in items])


@staff_api(["PATCH"])
def update_wish(request, wish_id: int):
    body = WishStatusSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    view = deps.update_wish().execute(
        wish_id, body.validated_data["status"], body.validated_data["note"]
    )
    return Response(wish_payload(view, staff=True))
