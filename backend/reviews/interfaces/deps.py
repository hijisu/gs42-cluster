from django.utils import timezone

from reviews.application.usecases import (
    CreateReviewUseCase,
    ListCourseReviewsUseCase,
    ListCoursesUseCase,
    ListTodoReviewsUseCase,
    Viewer,
)
from reviews.infrastructure.repositories import DjangoCourseRepository, DjangoReviewRepository


def viewer(user) -> Viewer:
    return Viewer(user_id=user.pk, intra_id=user.intra_id)


def list_courses() -> ListCoursesUseCase:
    return ListCoursesUseCase(
        DjangoCourseRepository(), DjangoReviewRepository(), timezone.localdate
    )


def list_todo() -> ListTodoReviewsUseCase:
    return ListTodoReviewsUseCase(
        DjangoCourseRepository(), DjangoReviewRepository(), timezone.localdate
    )


def list_course_reviews() -> ListCourseReviewsUseCase:
    return ListCourseReviewsUseCase(DjangoCourseRepository(), DjangoReviewRepository())


def create_review() -> CreateReviewUseCase:
    return CreateReviewUseCase(
        DjangoCourseRepository(), DjangoReviewRepository(), timezone.localdate
    )
