"""유스케이스 조립(Composition Root). 설정을 읽어 구현체를 연결한다."""

from django.conf import settings

from accounts.application.login import LoginAsMock, LoginWithProfile
from accounts.infrastructure.fortytwo import FortyTwoOAuthClient
from accounts.infrastructure.repository import DjangoUserRepository


def fortytwo_client() -> FortyTwoOAuthClient:
    return FortyTwoOAuthClient(
        uid=settings.FORTYTWO_UID,
        secret=settings.FORTYTWO_SECRET,
        redirect_uri=settings.FORTYTWO_REDIRECT_URI,
    )


def login_with_profile() -> LoginWithProfile:
    return LoginWithProfile(DjangoUserRepository(), settings.STAFF_INTRA_IDS)


def login_as_mock() -> LoginAsMock:
    return LoginAsMock(DjangoUserRepository())
