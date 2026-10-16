from rest_framework.permissions import BasePermission

from accounts.domain.role import Role


class IsStaff(BasePermission):
    """교육운영팀(role=staff)만 허용한다. /api/staff/* 에 사용."""

    message = "교육운영팀만 접근할 수 있습니다."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.role == Role.STAFF)
