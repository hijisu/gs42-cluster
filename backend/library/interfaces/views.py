from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from library.interfaces import deps
from library.interfaces.serializers import (
    BookPageSerializer,
    ReportSerializer,
    WishSerializer,
    book_payload,
    report_payload,
    wish_payload,
)


@api_view(["GET"])
def books(request):
    pagination = BookPageSerializer(data=request.query_params)
    pagination.is_valid(raise_exception=True)
    result = deps.search_books().execute(
        request.query_params.get("q", ""),
        request.query_params.get("category", ""),
        **pagination.validated_data,
    )
    return Response(
        {
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "categories": result.categories,
            "results": [book_payload(v.book, v.lost_count) for v in result.books],
        }
    )


@api_view(["GET"])
def book_detail(request, book_id: int):
    view = deps.get_book().execute(book_id)
    return Response(book_payload(view.book, view.lost_count))


@api_view(["POST"])
def create_report(request):
    body = ReportSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    view = deps.create_report().execute(request.user.pk, **body.validated_data)
    return Response(report_payload(view), status=status.HTTP_201_CREATED)


@api_view(["POST"])
def create_wish(request):
    body = WishSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    view = deps.create_wish().execute(request.user.pk, **body.validated_data)
    return Response(wish_payload(view), status=status.HTTP_201_CREATED)


@api_view(["GET"])
def my_requests(request):
    reports, wishes = deps.my_requests().execute(request.user.pk)
    return Response(
        {
            "reports": [report_payload(v) for v in reports],
            "wishes": [wish_payload(v) for v in wishes],
        }
    )
