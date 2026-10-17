from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied

from common.interfaces.csrf import LanDevCSRFCheck


class Session401Authentication(SessionAuthentication):
    """미인증 요청에 403 대신 401을 내려주기 위한 세션 인증."""

    def authenticate_header(self, request) -> str:
        return "Session"

    def enforce_csrf(self, request):
        check = LanDevCSRFCheck(lambda r: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise PermissionDenied(f"CSRF Failed: {reason}")
