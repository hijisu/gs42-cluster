"""유스케이스 조립(Composition Root)."""

from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from meetings.application.staff_usecases import (
    AssignMeetingUseCase,
    ConfirmMeetingUseCase,
    GetAvailabilityUseCase,
    ListMeetingTypesForStaffUseCase,
    ListStaffMeetingsUseCase,
    ProposeMeetingUseCase,
    ResetAvailabilityUseCase,
    SetAvailabilityUseCase,
    SetDefaultStaffUseCase,
)
from meetings.application.usecases import (
    AcceptMeetingProposalUseCase,
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
    DjangoStaffDirectory,
    DjangoStaffMeetingReadModel,
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


def list_staff_meetings() -> ListStaffMeetingsUseCase:
    return ListStaffMeetingsUseCase(DjangoStaffMeetingReadModel())


def assign_meeting() -> AssignMeetingUseCase:
    return AssignMeetingUseCase(
        DjangoMeetingRepository(), DjangoStaffDirectory(), DjangoStaffMeetingReadModel()
    )


def confirm_meeting() -> ConfirmMeetingUseCase:
    return ConfirmMeetingUseCase(
        DjangoMeetingRepository(),
        DjangoStaffDirectory(),
        DjangoStaffMeetingReadModel(),
        event_bus,
    )


def propose_meeting() -> ProposeMeetingUseCase:
    return ProposeMeetingUseCase(
        DjangoMeetingRepository(), DjangoStaffMeetingReadModel(), event_bus, timezone.now
    )


def get_availability() -> GetAvailabilityUseCase:
    return GetAvailabilityUseCase(DjangoAvailabilityRepository())


def set_availability() -> SetAvailabilityUseCase:
    return SetAvailabilityUseCase(DjangoAvailabilityRepository(), DjangoMeetingRepository())


def staff_meeting_types() -> ListMeetingTypesForStaffUseCase:
    return ListMeetingTypesForStaffUseCase(DjangoStaffMeetingReadModel())


def set_default_staff() -> SetDefaultStaffUseCase:
    return SetDefaultStaffUseCase(
        DjangoMeetingTypeRepository(), DjangoStaffDirectory(), DjangoStaffMeetingReadModel()
    )


def accept_meeting_proposal() -> AcceptMeetingProposalUseCase:
    return AcceptMeetingProposalUseCase(
        DjangoMeetingRepository(), DjangoMeetingReadModel(), event_bus, timezone.now
    )


def reset_availability() -> ResetAvailabilityUseCase:
    return ResetAvailabilityUseCase(DjangoAvailabilityRepository(), DjangoMeetingRepository())
