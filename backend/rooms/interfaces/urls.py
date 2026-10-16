from django.urls import path

from rooms.interfaces import views

room_urlpatterns = [
    path("availability", views.availability, name="rooms-availability"),
    path("rules", views.rules, name="rooms-rules"),
]

reservation_urlpatterns = [
    path("me", views.my_reservations, name="reservations-me"),
    path("<int:reservation_id>/cancel", views.cancel, name="reservation-cancel"),
]
