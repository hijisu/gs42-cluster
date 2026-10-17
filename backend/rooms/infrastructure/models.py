from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models

from rooms.domain.reservation import ReservationStatus
from rooms.domain.room import RoomStatus


class TsTzRange(models.Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


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
            ),
            # 승인된 예약끼리는 같은 장소에서 시간이 겹칠 수 없다(btree_gist 필요).
            ExclusionConstraint(
                name="room_res_no_overlap_approved",
                expressions=[
                    (TsTzRange("start_at", "end_at", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("room", RangeOperators.EQUAL),
                ],
                condition=models.Q(status="approved"),
            ),
        ]
        indexes = [
            models.Index(fields=["room", "start_at"]),
            models.Index(fields=["user", "-start_at"]),
        ]


class RoomRulesRow(models.Model):
    """이용 규칙 싱글턴(pk=1). 행이 없으면 코드의 기본값을 쓴다."""

    open_hour = models.PositiveSmallIntegerField()
    close_hour = models.PositiveSmallIntegerField()
    usage_rules = models.JSONField(default=list)

    class Meta:
        app_label = "rooms"
        db_table = "rooms_roomrules"


class RoomBlockRow(models.Model):
    """예약 차단 기간(시리즈). start_at/end_at 은 첫 회차, 반복 규칙은 domain.block 이 전개한다."""

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="+")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    reason = models.CharField(max_length=200)
    repeat = models.CharField(max_length=16, default="none")
    weekdays = models.JSONField(default=list)  # 0=월 … 6=일
    until = models.DateField(null=True, blank=True)
    skipped = models.JSONField(default=list)  # 건너뛴 회차 날짜(YYYY-MM-DD)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "rooms"
        db_table = "rooms_roomblock"
        ordering = ["start_at", "id"]
        indexes = [models.Index(fields=["room", "start_at"])]
