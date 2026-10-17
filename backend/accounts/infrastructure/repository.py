from accounts.domain.role import Role
from accounts.domain.user import UserAccount
from accounts.infrastructure.models import User


def _to_domain(row: User) -> UserAccount:
    return UserAccount(
        id=row.pk,
        intra_id=row.intra_id,
        name=row.name,
        role=Role(row.role),
        slack_id=row.slack_id,
        image_url=row.image_url,
    )


class DjangoUserRepository:
    def get_by_intra_id(self, intra_id: str) -> UserAccount | None:
        row = User.objects.filter(intra_id=intra_id).first()
        return _to_domain(row) if row else None

    def save(self, user: UserAccount) -> UserAccount:
        row, _ = User.objects.update_or_create(
            intra_id=user.intra_id,
            defaults={
                "name": user.name,
                "role": user.role.value,
                "slack_id": user.slack_id,
                "image_url": user.image_url,
            },
        )
        return _to_domain(row)

    def list_staff(self) -> list[UserAccount]:
        rows = User.objects.filter(role=Role.STAFF.value, is_active=True).order_by("name", "id")
        return [_to_domain(r) for r in rows]
