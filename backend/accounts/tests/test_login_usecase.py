"""유스케이스 테스트: DB 없이 인메모리 저장소로 검증한다."""

from accounts.application.login import LoginAsMock, LoginWithProfile
from accounts.application.ports import FortyTwoProfile
from accounts.domain.role import Role
from accounts.domain.user import UserAccount


class InMemoryUsers:
    def __init__(self):
        self.rows: dict[str, UserAccount] = {}

    def get_by_intra_id(self, intra_id):
        return self.rows.get(intra_id)

    def save(self, user):
        user.id = user.id or len(self.rows) + 1
        self.rows[user.intra_id] = user
        return user


def test_first_login_creates_student():
    users = InMemoryUsers()
    account = LoginWithProfile(users, []).execute(FortyTwoProfile("bob", "Bob"))
    assert account.role == Role.STUDENT and account.id == 1


def test_staff_ids_make_staff_and_role_is_re_resolved():
    users = InMemoryUsers()
    LoginWithProfile(users, []).execute(FortyTwoProfile("alice", "Alice"))
    account = LoginWithProfile(users, ["alice"]).execute(FortyTwoProfile("alice", "Alice K"))
    assert account.role == Role.STAFF and account.name == "Alice K"
    assert len(users.rows) == 1


def test_role_downgrade_when_removed_from_staff_list():
    users = InMemoryUsers()
    LoginWithProfile(users, ["alice"]).execute(FortyTwoProfile("alice", "Alice"))
    account = LoginWithProfile(users, []).execute(FortyTwoProfile("alice", "Alice"))
    assert account.role == Role.STUDENT


def test_mock_login_seeds_accounts():
    users = InMemoryUsers()
    assert LoginAsMock(users).execute(Role.STUDENT).intra_id == "student"
    assert LoginAsMock(users).execute(Role.STAFF).role == Role.STAFF
