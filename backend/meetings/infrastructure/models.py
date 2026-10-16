from django.conf import settings
from django.db import models

from meetings.domain.meeting import MeetingStatus


class MeetingType(models.Model):
    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    default_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "meetings"
        ordering = ["sort_order", "id"]


class AvailabilitySlot(models.Model):
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    start_at = models.DateTimeField()

    class Meta:
        app_label = "meetings"
        constraints = [
            models.UniqueConstraint(fields=["staff", "start_at"], name="uniq_staff_slot_start")
        ]
        indexes = [models.Index(fields=["start_at"])]


class MeetingRequestRow(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    type = models.ForeignKey(MeetingType, on_delete=models.PROTECT, related_name="+")
    slot_at = models.DateTimeField()
    content = models.TextField(blank=True)
    notify_slack = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in MeetingStatus],
        default=MeetingStatus.PENDING.value,
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    location = models.CharField(max_length=128, blank=True)
    proposed_at = models.DateTimeField(null=True, blank=True)
    staff_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "meetings"
        db_table = "meetings_meetingrequest"
        constraints = [
            # 같은 담당자의 같은 시각에 확정 면담은 하나만. 중복 확정의 최종 방어선.
            models.UniqueConstraint(
                fields=["staff", "slot_at"],
                condition=models.Q(status="confirmed"),
                name="uniq_confirmed_staff_slot",
            )
        ]
        indexes = [
            models.Index(fields=["student", "-slot_at"]),
            models.Index(fields=["status", "slot_at"]),
        ]
