from rest_framework.decorators import api_view, authentication_classes, permission_classes

from accounts.interfaces.authentication import Session401Authentication
from accounts.interfaces.permissions import IsStaff


def staff_api(methods):
    """/api/staff/* 뷰용: 운영팀만 허용(비로그인 401, 교육생 403)."""

    def decorator(view):
        view = permission_classes([IsStaff])(view)
        view = authentication_classes([Session401Authentication])(view)
        return api_view(methods)(view)

    return decorator
