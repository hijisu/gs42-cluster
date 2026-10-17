from django.utils import timezone
from rest_framework import serializers

from reviews.application.usecases import CourseView, ReviewItem


class CreateReviewSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=200)
    good = serializers.CharField(allow_blank=True, max_length=5000, default="")
    bad = serializers.CharField(allow_blank=True, max_length=5000, default="")
    recommend_to = serializers.CharField(allow_blank=True, max_length=5000, default="")
    tags = serializers.ListField(
        child=serializers.CharField(max_length=40), max_length=20, default=list
    )
    anonymous = serializers.BooleanField(default=False)


def course_payload(v: CourseView) -> dict:
    c = v.course
    return {
        "id": c.id,
        "name": c.name,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "location": c.location,
        "intro": c.intro,
        "status": c.phase(timezone.localdate()).value,
        "review_deadline": c.review_deadline,
        "average_rating": v.stats.average_rating,
        "review_count": v.stats.review_count,
        "participating": v.participating,
        "reviewed": v.reviewed,
        "can_review": v.can_review,
    }


def review_payload(item: ReviewItem) -> dict:
    r = item.review
    return {
        "id": r.id,
        "course_id": r.course_id,
        "rating": r.rating,
        "title": r.title,
        "good": r.good,
        "bad": r.bad,
        "recommend_to": r.recommend_to,
        "tags": r.tags,
        "anonymous": r.anonymous,
        # 익명 후기는 작성자 정보를 아예 내려주지 않는다.
        "author": None if r.author_intra_id is None else {"intra_id": r.author_intra_id},
        "mine": item.mine,
        "created_at": r.created_at,
    }
