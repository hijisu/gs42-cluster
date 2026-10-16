from collections.abc import Iterable

from accounts.application.ports import FortyTwoProfile, UserRepository
from accounts.domain.role import Role, resolve_role
from accounts.domain.user import UserAccount


class LoginWithProfile:
    """42 프로필로 사용자를 만들거나 갱신한다. 로그인할 때마다 역할을 다시 판별한다."""

    def __init__(self, users: UserRepository, staff_intra_ids: Iterable[str]) -> None:
        self._users = users
        self._staff_intra_ids = list(staff_intra_ids)

    def execute(self, profile: FortyTwoProfile) -> UserAccount:
        role = resolve_role(profile.intra_id, self._staff_intra_ids, profile.is_staff)
        user = self._users.get_by_intra_id(profile.intra_id)
        if user is None:
            user = UserAccount(intra_id=profile.intra_id, name=profile.name, role=role)
        else:
            user.name = profile.name
            user.role = role
        return self._users.save(user)


class LoginAsMock:
    """개발용 모의 로그인(시드 계정 student/staff). 허용 여부는 interfaces에서 판단한다."""

    SEED = {Role.STUDENT: ("student", "모의 교육생"), Role.STAFF: ("staff", "모의 운영팀")}

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, role: Role) -> UserAccount:
        intra_id, name = self.SEED[role]
        user = self._users.get_by_intra_id(intra_id)
        if user is None:
            user = UserAccount(intra_id=intra_id, name=name, role=role)
        else:
            user.role = role
        return self._users.save(user)
