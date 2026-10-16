from django.conf import settings
from django.db import models

from rooms.domain.reservation import ReservationStatus
from rooms.domain.room import RoomStatus


class Room(models.Model):
    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    capacity_note = models.CharField(max_length=64, blank=True)
    equipment = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in RoomStatus],
        default=RoomStatus.OPEN.value,
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "rooms"
        ordering = ["sort_order", "id"]


class RoomReservationRow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="+")
    requested_room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="+")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    purpose = models.CharField(max_length=100)
    headcount = models.PositiveSmallIntegerField()
    note = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in ReservationStatus],
        default=ReservationStatus.PENDING.value,
    )
    reject_reason = models.TextField(blank=True)
    created_by_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "rooms"
        db_table = "rooms_roomreservation"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")), name="room_res_end_after_start"
            )
        ]
        indexes = [
            models.Index(fields=["room", "start_at"]),
            models.Index(fields=["user", "-start_at"]),
        ]
