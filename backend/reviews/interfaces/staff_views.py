"""운영팀 전용 교육과정·후기 API. 모든 뷰에 IsStaff를 적용한다."""

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from accounts.interfaces.decorators import staff_api
from reviews.application.staff_usecases import CreateCourseCommand
from reviews.domain.course import ReviewTarget
from reviews.interfaces import staff_deps as deps
from reviews.interfaces.staff_serializers import (
    CoursePatchSerializer,
    CourseWriteSerializer,
    ParticipantsSerializer,
    ReviewRequestSerializer,
    staff_course_payload,
)


@staff_api(["GET", "POST"])
def courses(request):
    if request.method == "GET":
        return Response([staff_course_payload(v) for v in deps.list_courses().execute()])
    body = CourseWriteSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    with transaction.atomic():
        view = deps.create_course().execute(
            CreateCourseCommand(
                name=data["name"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                location=data["location"],
                intro=data["intro"],
                review_deadline=data["review_deadline"],
                intra_ids=data["intra_ids"],
                csv=data["csv"],
            )
        )
    return Response(staff_course_payload(view, detail=True), status=status.HTTP_201_CREATED)


@staff_api(["GET", "PATCH"])
def course_detail(request, course_id: int):
    if request.method == "GET":
        return Response(staff_course_payload(deps.get_course().execute(course_id), detail=True))
    body = CoursePatchSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    changes = dict(body.validated_data)
    with transaction.atomic():
        view = deps.update_course().execute(course_id, changes)
    return Response(staff_course_payload(view, detail=True))


@staff_api(["POST"])
def add_participants(request, course_id: int):
    body = ParticipantsSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    with transaction.atomic():
        result = deps.add_participants().execute(
            course_id,
            intra_ids=body.validated_data.get("intra_ids", []),
            csv=body.validated_data.get("csv", ""),
        )
    return Response(
        {
            "added": result.added,
            "existing": result.existing,
            "course": staff_course_payload(result.view, detail=True),
        }
    )


@staff_api(["DELETE"])
def remove_participant(request, course_id: int, intra_id: str):
    """참여자 제거. 이미 쓴 후기는 남고 작성률에서만 빠진다(`had_review`로 알린다)."""
    with transaction.atomic():
        result = deps.remove_participant().execute(course_id, intra_id)
    return Response(
        {"had_review": result.had_review, "course": staff_course_payload(result.view, detail=True)}
    )


@staff_api(["POST"])
def review_request(request, course_id: int):
    body = ReviewRequestSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    result = deps.request_reviews().execute(
        course_id, ReviewTarget(body.validated_data["target"]), body.validated_data["message"]
    )
    return Response(
        {
            "course_id": result.course_id,
            "target": result.target.value,
            "recipient_count": len(result.recipients),
            "recipients": result.recipients,
        }
    )
