from dataclasses import dataclass
from typing import Protocol

from accounts.domain.user import UserAccount


@dataclass(frozen=True)
class FortyTwoProfile:
    intra_id: str
    name: str
    is_staff: bool = False
    image_url: str = ""


class FortyTwoClient(Protocol):
    def authorize_url(self, state: str) -> str: ...

    def fetch_profile(self, code: str) -> FortyTwoProfile:
        """인가 코드를 토큰으로 교환하고 /v2/me 프로필을 반환한다. 실패 시 AuthenticationFailed."""
        ...


class UserRepository(Protocol):
    def get_by_intra_id(self, intra_id: str) -> UserAccount | None: ...

    def save(self, user: UserAccount) -> UserAccount: ...

    def list_staff(self) -> list[UserAccount]: ...
