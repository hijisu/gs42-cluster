from django.conf import settings
from django.db import models

from library.domain.report import ReportKind, ReportStatus
from library.domain.wish import WishStatus


class BookRow(models.Model):
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=40)
    quantity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True)
    cover_url = models.URLField(max_length=500, blank=True)
    link_url = models.URLField(max_length=500, blank=True)
    pub_date = models.CharField(max_length=20, blank=True)

    class Meta:
        app_label = "library"
        db_table = "library_book"
        ordering = ["code"]
        indexes = [models.Index(fields=["category"])]


class BookReportRow(models.Model):
    book = models.ForeignKey(BookRow, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=16, choices=[(k.value, k.name) for k in ReportKind])
    detail = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in ReportStatus],
        default=ReportStatus.RECEIVED.value,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "library"
        db_table = "library_report"
        ordering = ["-created_at", "-id"]


class WishRow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=300, blank=True)
    reason = models.TextField(blank=True)
    link_url = models.URLField(max_length=500, blank=True)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in WishStatus],
        default=WishStatus.REQUESTED.value,
    )
    staff_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "library"
        db_table = "library_wish"
        ordering = ["-created_at", "-id"]
