from django.urls import include, path

from accounts.interfaces.urls import auth_urlpatterns, staff_urlpatterns
from common.interfaces.views import health
from meetings.interfaces import views as meeting_views
from meetings.interfaces.staff_urls import staff_urlpatterns as meeting_staff_urlpatterns
from meetings.interfaces.urls import urlpatterns as meeting_urlpatterns
from rooms.interfaces import views as room_views
from rooms.interfaces.urls import reservation_urlpatterns, room_urlpatterns
from reviews.interfaces import views as review_views
from reviews.interfaces.urls import course_urlpatterns, review_urlpatterns

urlpatterns = [
    path("health", health, name="health"),
    path("auth/", include(auth_urlpatterns)),
    path("meetings", meeting_views.create_meeting, name="meeting-create"),
    path("meetings/", include(meeting_urlpatterns)),
    path("courses", review_views.courses, name="courses"),
    path("courses/", include(course_urlpatterns)),
    path("reviews", review_views.create_review, name="review-create"),
    path("reviews/", include(review_urlpatterns)),
    # 운영팀 전용 API. 모든 /api/staff/* 뷰는 IsStaff를 적용한다.
    path("rooms", room_views.list_rooms, name="rooms"),
    path("rooms/", include(room_urlpatterns)),
    path("reservations", room_views.create_reservation, name="reservation-create"),
    path("reservations/", include(reservation_urlpatterns)),
    path("staff/", include(staff_urlpatterns + meeting_staff_urlpatterns)),
]
