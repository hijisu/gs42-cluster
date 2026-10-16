from django.urls import include, path

from accounts.interfaces.urls import auth_urlpatterns, staff_urlpatterns
from common.interfaces.views import health
from meetings.interfaces import views as meeting_views
from meetings.interfaces.staff_urls import staff_urlpatterns as meeting_staff_urlpatterns
from meetings.interfaces.urls import urlpatterns as meeting_urlpatterns

urlpatterns = [
    path("health", health, name="health"),
    path("auth/", include(auth_urlpatterns)),
    path("meetings", meeting_views.create_meeting, name="meeting-create"),
    path("meetings/", include(meeting_urlpatterns)),
    # 운영팀 전용 API. 모든 /api/staff/* 뷰는 IsStaff를 적용한다.
    path("staff/", include(staff_urlpatterns + meeting_staff_urlpatterns)),
]
