from rest_framework.authentication import SessionAuthentication


class Session401Authentication(SessionAuthentication):
    """미인증 요청에 403 대신 401을 내려주기 위한 세션 인증."""

    def authenticate_header(self, request) -> str:
        return "Session"
