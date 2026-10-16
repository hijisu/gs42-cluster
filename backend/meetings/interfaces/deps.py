"""유스케이스 조립(Composition Root)."""

from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from meetings.application.usecases import (
    CancelMeetingUseCase,
    GetSlotsUseCase,
    ListMyMeetingsUseCase,
    RequestMeetingUseCase,
)
from meetings.infrastructure.repositories import (
    DjangoAvailabilityRepository,
    DjangoMeetingReadModel,
    DjangoMeetingRepository,
    DjangoMeetingTypeRepository,
)


def meeting_types() -> DjangoMeetingTypeRepository:
    return DjangoMeetingTypeRepository()


def get_slots() -> GetSlotsUseCase:
    return GetSlotsUseCase(DjangoAvailabilityRepository(), DjangoMeetingRepository(), timezone.now)


def request_meeting() -> RequestMeetingUseCase:
    return RequestMeetingUseCase(
        meetings=DjangoMeetingRepository(),
        types=DjangoMeetingTypeRepository(),
        availability=DjangoAvailabilityRepository(),
        read_model=DjangoMeetingReadModel(),
        events=event_bus,
        clock=timezone.now,
    )


def cancel_meeting() -> CancelMeetingUseCase:
    return CancelMeetingUseCase(DjangoMeetingRepository(), DjangoMeetingReadModel(), event_bus)


def list_my_meetings() -> ListMyMeetingsUseCase:
    return ListMyMeetingsUseCase(DjangoMeetingReadModel())
