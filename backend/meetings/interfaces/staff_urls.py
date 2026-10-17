from django.urls import path

from meetings.interfaces import staff_views as views

staff_urlpatterns = [
    path("meetings", views.list_meetings, name="staff-meetings"),
    path("meetings/<int:meeting_id>/assign", views.assign, name="staff-meeting-assign"),
    path("meetings/<int:meeting_id>/confirm", views.confirm, name="staff-meeting-confirm"),
    path("meetings/<int:meeting_id>/propose", views.propose, name="staff-meeting-propose"),
    path("meetings/<int:meeting_id>/cancel", views.cancel, name="staff-meeting-cancel"),
    path("availability", views.availability, name="staff-availability"),
    path("meeting-types", views.meeting_types, name="staff-meeting-types"),
]
