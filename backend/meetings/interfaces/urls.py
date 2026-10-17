from django.urls import path

from meetings.interfaces import views

urlpatterns = [
    path("types", views.meeting_types, name="meeting-types"),
    path("slots", views.slots, name="meeting-slots"),
    path("me", views.my_meetings, name="meeting-me"),
    path("<int:meeting_id>/cancel", views.cancel, name="meeting-cancel"),
    path("<int:meeting_id>/accept", views.accept_proposal, name="meeting-accept"),
]
