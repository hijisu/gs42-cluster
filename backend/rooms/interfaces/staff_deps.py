from django.utils import timezone

from common.infrastructure.event_bus import event_bus
from rooms.application.block_usecases import (
    CreateBlockUseCase,
    DeleteBlockUseCase,
    ListBlocksUseCase,
    SkipOccurrenceUseCase,
    UpdateBlockUseCase,
    UpdateOccurrenceUseCase,
)
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
    DjangoBlockRepository,
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
    return ApproveReservationUseCase(*_base(), event_bus, DjangoBlockRepository())


def reject() -> RejectReservationUseCase:
    return RejectReservationUseCase(*_base(), event_bus)


def reassign() -> ReassignReservationUseCase:
    return ReassignReservationUseCase(*_base(), event_bus, DjangoBlockRepository())


def book() -> StaffBookUseCase:
    return StaffBookUseCase(
        *_base(),
        event_bus,
        timezone.now,
        DjangoRulesRepository().get,
        DjangoBlockRepository(),
    )


def update_rules() -> UpdateRulesUseCase:
    return UpdateRulesUseCase(DjangoRulesRepository())


def create_room() -> CreateRoomUseCase:
    return CreateRoomUseCase(DjangoRoomRepository())


def update_room() -> UpdateRoomUseCase:
    return UpdateRoomUseCase(DjangoRoomRepository())


def _block_base():
    return DjangoBlockRepository(), DjangoReservationRepository(), DjangoRoomRepository()


def create_block() -> CreateBlockUseCase:
    return CreateBlockUseCase(*_block_base())


def list_blocks() -> ListBlocksUseCase:
    return ListBlocksUseCase(DjangoBlockRepository())


def update_block() -> UpdateBlockUseCase:
    return UpdateBlockUseCase(*_block_base())


def delete_block() -> DeleteBlockUseCase:
    return DeleteBlockUseCase(DjangoBlockRepository())


def skip_occurrence() -> SkipOccurrenceUseCase:
    return SkipOccurrenceUseCase(*_block_base())


def update_occurrence() -> UpdateOccurrenceUseCase:
    return UpdateOccurrenceUseCase(*_block_base())
