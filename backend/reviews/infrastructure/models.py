from django.conf import settings
from django.db import models

from reviews.domain.course import CourseStatus


class CourseRow(models.Model):
    name = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=128, blank=True)
    intro = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.name) for s in CourseStatus],
        default=CourseStatus.UPCOMING.value,
    )
    review_deadline = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "reviews"
        db_table = "reviews_course"
        ordering = ["-start_date", "-id"]


class CourseParticipant(models.Model):
    """가입 전 사용자도 등록할 수 있도록 intra_id 문자열로 보관한다(소문자 정규화)."""

    course = models.ForeignKey(CourseRow, on_delete=models.CASCADE, related_name="participants")
    intra_id = models.CharField(max_length=64)

    class Meta:
        app_label = "reviews"
        constraints = [
            models.UniqueConstraint(fields=["course", "intra_id"], name="uniq_course_participant")
        ]
        indexes = [models.Index(fields=["intra_id"])]


class ReviewRow(models.Model):
    course = models.ForeignKey(CourseRow, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    anonymous = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    good = models.TextField(blank=True)
    bad = models.TextField(blank=True)
    recommend_to = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "reviews"
        db_table = "reviews_review"
        constraints = [
            models.UniqueConstraint(fields=["course", "author"], name="uniq_review_per_author"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_1_5"
            ),
        ]
        indexes = [models.Index(fields=["course", "-created_at"])]
