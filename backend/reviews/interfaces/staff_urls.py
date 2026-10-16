from django.urls import path

from reviews.interfaces import staff_views as views

staff_urlpatterns = [
    path("courses", views.courses, name="staff-courses"),
    path("courses/<int:course_id>", views.course_detail, name="staff-course-detail"),
    path(
        "courses/<int:course_id>/participants",
        views.add_participants,
        name="staff-course-participants",
    ),
    path(
        "courses/<int:course_id>/review-request",
        views.review_request,
        name="staff-course-review-request",
    ),
]
