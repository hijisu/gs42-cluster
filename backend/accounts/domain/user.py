from dataclasses import dataclass

from accounts.domain.role import Role


@dataclass
class UserAccount:
    intra_id: str
    name: str
    role: Role
    slack_id: str | None = None
    id: int | None = None

    @property
    def is_staff(self) -> bool:
        return self.role == Role.STAFF
