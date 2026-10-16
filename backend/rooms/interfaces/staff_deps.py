from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from rooms.application.staff_usecases import (
    ApproveReservationUseCase,
    CreateRoomUseCase,
    ListStaffReservationsUseCase,
    ReassignReservationUseCase,
    RejectReservationUseCase,
    StaffBookUseCase,
    UpdateRoomUseCase,
    UpdateRulesUseCase,
)
from rooms.infrastructure.repositories import (
    DjangoReservationRepository,
    DjangoRoomRepository,
    DjangoRulesRepository,
    DjangoStaffReadModel,
)


def _base():
    return DjangoRoomRepository(), DjangoReservationRepository(), DjangoStaffReadModel()


def list_reservations() -> ListStaffReservationsUseCase:
    return ListStaffReservationsUseCase(*_base(), timezone.now)


def approve() -> ApproveReservationUseCase:
    return ApproveReservationUseCase(*_base(), event_bus)


def reject() -> RejectReservationUseCase:
    return RejectReservationUseCase(*_base(), event_bus)


def reassign() -> ReassignReservationUseCase:
    return ReassignReservationUseCase(*_base(), event_bus)


def book() -> StaffBookUseCase:
    return StaffBookUseCase(*_base(), event_bus, timezone.now, DjangoRulesRepository().get)


def update_rules() -> UpdateRulesUseCase:
    return UpdateRulesUseCase(DjangoRulesRepository())


def create_room() -> CreateRoomUseCase:
    return CreateRoomUseCase(DjangoRoomRepository())


def update_room() -> UpdateRoomUseCase:
    return UpdateRoomUseCase(DjangoRoomRepository())
