from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from reviews.application.usecases import CreateReviewCommand
from reviews.interfaces import deps
from reviews.interfaces.serializers import CreateReviewSerializer, course_payload, review_payload


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


@api_view(["POST"])
def create_review(request):
    body = CreateReviewSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    item = deps.create_review().execute(
        CreateReviewCommand(viewer=deps.viewer(request.user), **body.validated_data)
    )
    return Response(review_payload(item), status=status.HTTP_201_CREATED)
