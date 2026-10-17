from django.utils import timezone
from rest_framework import serializers

from reviews.application.staff_usecases import StaffCourseView
from reviews.domain.course import ReviewTarget


class CourseWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    location = serializers.CharField(allow_blank=True, max_length=128, default="")
    intro = serializers.CharField(allow_blank=True, max_length=5000, default="")
    review_deadline = serializers.DateField(allow_null=True, default=None)
    intra_ids = serializers.ListField(
        child=serializers.CharField(max_length=64), max_length=500, default=list
    )
    csv = serializers.CharField(allow_blank=True, max_length=100_000, default="")


class CoursePatchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    location = serializers.CharField(allow_blank=True, max_length=128, required=False)
    intro = serializers.CharField(allow_blank=True, max_length=5000, required=False)
    review_deadline = serializers.DateField(allow_null=True, required=False)


class ParticipantsSerializer(serializers.Serializer):
    intra_ids = serializers.ListField(
        child=serializers.CharField(max_length=64), max_length=500, required=False
    )
    csv = serializers.CharField(allow_blank=True, max_length=100_000, required=False)

    def validate(self, attrs):
        if not attrs.get("intra_ids") and not attrs.get("csv"):
            raise serializers.ValidationError("intra_ids 또는 csv 중 하나는 필요합니다")
        return attrs


class ReviewRequestSerializer(serializers.Serializer):
    target = serializers.ChoiceField(choices=[t.value for t in ReviewTarget])
    message = serializers.CharField(allow_blank=True, max_length=500, default="")


def staff_course_payload(v: StaffCourseView, detail: bool = False) -> dict:
    c = v.course
    data = {
        "id": c.id,
        "name": c.name,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "location": c.location,
        "intro": c.intro,
        "status": c.phase(timezone.localdate()).value,
        "review_deadline": c.review_deadline,
        "participant_count": v.participant_count,
        "reviewed_count": v.reviewed_count,
        "pending_count": v.participant_count - v.reviewed_count,
        "review_rate": v.review_rate,
    }
    if detail:
        data["participants"] = [
            {"intra_id": i, "reviewed": i in v.reviewed} for i in sorted(c.participants)
        ]
    return data
