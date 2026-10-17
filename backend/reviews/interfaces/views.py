from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from reviews.application.usecases import CreateReviewCommand, UpdateReviewCommand
from reviews.interfaces import deps
from reviews.interfaces.serializers import (
    CreateReviewSerializer,
    UpdateReviewSerializer,
    course_payload,
    review_payload,
)


@api_view(["GET"])
def courses(request):
    views = deps.list_courses().execute(deps.viewer(request.user))
    return Response([course_payload(v) for v in views])


@api_view(["GET"])
def course_reviews(request, course_id: int):
    items = deps.list_course_reviews().execute(course_id, deps.viewer(request.user))
    return Response([review_payload(i) for i in items])


@api_view(["GET"])
def todo(request):
    views = deps.list_todo().execute(deps.viewer(request.user))
    return Response([course_payload(v) for v in views])


@api_view(["PATCH"])
def update_review(request, review_id: int):
    """본인 후기 수정(삭제는 제공하지 않는다)."""
    body = UpdateReviewSerializer(data=request.data, partial=True)
    body.is_valid(raise_exception=True)
    item = deps.update_review().execute(
        UpdateReviewCommand(
            viewer=deps.viewer(request.user),
            review_id=review_id,
            changes=dict(body.validated_data),
        )
    )
    return Response(review_payload(item))


@api_view(["POST"])
def create_review(request):
    body = CreateReviewSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    item = deps.create_review().execute(
        CreateReviewCommand(viewer=deps.viewer(request.user), **body.validated_data)
    )
    return Response(review_payload(item), status=status.HTTP_201_CREATED)
