import ipaddress
from urllib.parse import urlsplit

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import CSRFCheck


def _is_private_ip_origin(origin: str) -> bool:
    try:
        host = urlsplit(origin).hostname
        address = ipaddress.ip_address(host) if host else None
    except ValueError:
        return False
    return bool(address and (address.is_private or address.is_loopback))


class LanDevOriginMixin:
    """개발 모드(DEBUG)에서만 사설망 IP로 접속한 프론트(예: http://192.168.0.7:5173)를 신뢰한다.

    같은 네트워크의 다른 기기에서 개발 서버를 테스트할 수 있게 하려는 것이다.
    운영(DEBUG=false)에서는 표준 CsrfViewMiddleware와 똑같이 동작한다(FRONTEND_ORIGIN만 신뢰).
    """

    def _origin_verified(self, request):
        if settings.DEBUG and _is_private_ip_origin(request.META["HTTP_ORIGIN"]):
            return True
        return super()._origin_verified(request)


class LanDevCsrfMiddleware(LanDevOriginMixin, CsrfViewMiddleware):
    """Django 미들웨어(관리자·폼 등) 경로."""


class LanDevCSRFCheck(LanDevOriginMixin, CSRFCheck):
    """DRF 세션 인증(API) 경로. DRF는 별도의 CSRFCheck를 쓰므로 같은 규칙을 적용한다."""
