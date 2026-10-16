from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from reviews.application.staff_usecases import (
    AddParticipantsUseCase,
    CreateCourseUseCase,
    GetStaffCourseUseCase,
    ListStaffCoursesUseCase,
    RequestReviewsUseCase,
    UpdateCourseUseCase,
)
from reviews.infrastructure.repositories import DjangoCourseRepository, DjangoReviewRepository


def _repos():
    return DjangoCourseRepository(), DjangoReviewRepository()


def list_courses() -> ListStaffCoursesUseCase:
    return ListStaffCoursesUseCase(*_repos())


def get_course() -> GetStaffCourseUseCase:
    return GetStaffCourseUseCase(*_repos())


def create_course() -> CreateCourseUseCase:
    return CreateCourseUseCase(*_repos())


def update_course() -> UpdateCourseUseCase:
    return UpdateCourseUseCase(*_repos())


def add_participants() -> AddParticipantsUseCase:
    return AddParticipantsUseCase(*_repos())


def request_reviews() -> RequestReviewsUseCase:
    return RequestReviewsUseCase(*_repos(), event_bus, timezone.localdate)
