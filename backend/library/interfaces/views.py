from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from library.interfaces import deps
from library.interfaces.serializers import (
    ReportSerializer,
    WishSerializer,
    book_payload,
    report_payload,
    wish_payload,
)


@api_view(["GET"])
def books(request):
    result = deps.search_books().execute(
        request.query_params.get("q", ""), request.query_params.get("category", "")
    )
    return Response(
        {
            "total": result.total,
            "categories": result.categories,
            "results": [book_payload(b) for b in result.books],
        }
    )


@api_view(["GET"])
def book_detail(request, book_id: int):
    return Response(book_payload(deps.get_book().execute(book_id)))


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
