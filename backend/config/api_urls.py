from django.urls import include, path

from accounts.interfaces.urls import auth_urlpatterns, staff_urlpatterns
from common.interfaces.views import health

urlpatterns = [
    path("health", health, name="health"),
    path("auth/", include(auth_urlpatterns)),
    # 운영팀 전용 API. 모든 /api/staff/* 뷰는 IsStaff를 적용한다.
    path("staff/", include(staff_urlpatterns)),
]
