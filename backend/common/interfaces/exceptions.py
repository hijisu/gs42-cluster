"""도메인 오류를 {"code": ...} 본문과 HTTP 상태로 변환한다."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from common.domain.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
)

_STATUS = (
    (ConflictError, status.HTTP_409_CONFLICT),
    (ForbiddenError, status.HTTP_403_FORBIDDEN),
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (InvalidRequestError, status.HTTP_400_BAD_REQUEST),
)


def api_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        http_status = next((s for cls, s in _STATUS if isinstance(exc, cls)), 400)
        return Response({"code": exc.code, "detail": str(exc)}, status=http_status)
    return exception_handler(exc, context)
