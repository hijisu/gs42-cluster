import logging
import secrets

from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.domain.errors import AuthenticationFailed
from accounts.domain.role import Role
from accounts.infrastructure.models import User
from accounts.interfaces import deps
from accounts.interfaces.authentication import Session401Authentication
from accounts.interfaces.permissions import IsStaff
from accounts.interfaces.serializers import MockLoginSerializer, UserSerializer

BACKEND = "django.contrib.auth.backends.ModelBackend"
STATE_KEY = "oauth_state"
logger = logging.getLogger(__name__)


def _error(code: str, http_status: int) -> Response:
    return Response({"code": code}, status=http_status)


def _frontend_redirect(path: str = "/", error: str | None = None) -> HttpResponseRedirect:
    url = f"{settings.FRONTEND_ORIGIN}{path}"
    if error:
        url = f"{settings.FRONTEND_ORIGIN}/login?error={error}"
    return HttpResponseRedirect(url)


def _start_session(request, account) -> None:
    login(request, User.objects.get(pk=account.id), backend=BACKEND)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_redirect(request):
    if not settings.FORTYTWO_UID:
        return _error("oauth_not_configured", status.HTTP_503_SERVICE_UNAVAILABLE)
    state = secrets.token_urlsafe(24)
    request.session[STATE_KEY] = state
    return HttpResponseRedirect(deps.fortytwo_client().authorize_url(state))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def callback(request):
    expected = request.session.pop(STATE_KEY, None)
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not expected or not state or not secrets.compare_digest(expected, state) or not code:
        return _frontend_redirect(error="invalid_state")
    try:
        profile = deps.fortytwo_client().fetch_profile(code)
    except AuthenticationFailed as exc:
        # 코드·토큰·응답 본문은 남기지 않는다. 단계/상태/원인만 기록한다.
        logger.warning(
            "42 OAuth 로그인 실패 stage=%s status=%s reason=%s",
            exc.stage or "-",
            exc.status if exc.status is not None else "-",
            exc.reason or "-",
        )
        return _frontend_redirect(error="auth_failed")
    account = deps.login_with_profile().execute(profile)
    _start_session(request, account)
    return _frontend_redirect("/")


@api_view(["GET"])
@authentication_classes([Session401Authentication])
@permission_classes([IsAuthenticated])
def me(request):
    get_token(request)  # CSRF 쿠키 발급 (이후 POST 요청용)
    user = request.user
    return Response(
        UserSerializer(
            {
                "id": user.pk,
                "intra_id": user.intra_id,
                "name": user.name,
                "image_url": user.image_url,
                "role": user.role,
                "slack_id": user.slack_id,
            }
        ).data
    )


@api_view(["POST"])
@authentication_classes([Session401Authentication])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def mock_login(request):
    if not settings.MOCK_LOGIN_ENABLED:
        return _error("not_found", status.HTTP_404_NOT_FOUND)
    serializer = MockLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    account = deps.login_as_mock().execute(Role(serializer.validated_data["role"]))
    _start_session(request, account)
    return Response({"intra_id": account.intra_id, "role": account.role.value})


@api_view(["GET"])
@authentication_classes([Session401Authentication])
@permission_classes([IsStaff])
def staff_ping(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@authentication_classes([Session401Authentication])
@permission_classes([IsStaff])
def staff_members(request):
    members = deps.list_staff_members().execute()
    return Response([{"id": m.id, "intra_id": m.intra_id, "name": m.name} for m in members])
