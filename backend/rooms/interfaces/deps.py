"""유스케이스 조립(Composition Root)."""

from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from rooms.application.usecases import (
    CancelReservationUseCase,
    GetAvailabilityUseCase,
    GetRulesUseCase,
    ListMyReservationsUseCase,
    ListRoomsUseCase,
    RequestReservationUseCase,
)
from rooms.infrastructure.repositories import (
    DjangoBlockRepository,
    DjangoReservationReadModel,
    DjangoReservationRepository,
    DjangoRoomRepository,
    DjangoRulesRepository,
)


def list_rooms() -> ListRoomsUseCase:
    return ListRoomsUseCase(DjangoRoomRepository())


def get_rules() -> GetRulesUseCase:
    return GetRulesUseCase(DjangoRulesRepository().get)


def get_availability() -> GetAvailabilityUseCase:
    return GetAvailabilityUseCase(
        DjangoRoomRepository(),
        DjangoReservationRepository(),
        DjangoRulesRepository().get,
        DjangoBlockRepository(),
    )


def request_reservation() -> RequestReservationUseCase:
    return RequestReservationUseCase(
        DjangoRoomRepository(),
        DjangoReservationRepository(),
        DjangoReservationReadModel(),
        event_bus,
        timezone.now,
        DjangoRulesRepository().get,
        DjangoBlockRepository(),
    )


def cancel_reservation() -> CancelReservationUseCase:
    return CancelReservationUseCase(
        DjangoReservationRepository(), DjangoReservationReadModel(), event_bus
    )


def list_my_reservations() -> ListMyReservationsUseCase:
    return ListMyReservationsUseCase(DjangoReservationRepository(), DjangoReservationReadModel())
