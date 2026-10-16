from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from accounts.domain.role import Role


class UserManager(BaseUserManager):
    def create_user(self, intra_id, **extra):
        user = self.model(intra_id=intra_id, **extra)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    intra_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    role = models.CharField(max_length=16, choices=[(r.value, r.name) for r in Role])
    slack_id = models.CharField(max_length=32, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "intra_id"
    objects = UserManager()

    class Meta:
        app_label = "accounts"
        db_table = "accounts_user"

    def __str__(self) -> str:
        return self.intra_id
