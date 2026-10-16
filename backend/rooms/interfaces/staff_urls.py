from django.urls import path

from rooms.interfaces import staff_views as views

staff_urlpatterns = [
    path("reservations", views.reservations, name="staff-reservations"),
    path(
        "reservations/<int:reservation_id>/approve", views.approve, name="staff-reservation-approve"
    ),
    path("reservations/<int:reservation_id>/reject", views.reject, name="staff-reservation-reject"),
    path(
        "reservations/<int:reservation_id>/reassign",
        views.reassign,
        name="staff-reservation-reassign",
    ),
    path("rooms", views.create_room, name="staff-room-create"),
    path("rooms/rules", views.rules, name="staff-room-rules"),
    path("rooms/<int:room_id>", views.update_room, name="staff-room-update"),
]
