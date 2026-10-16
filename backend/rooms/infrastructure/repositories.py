from datetime import datetime

from rooms.application.ports import ReservationView, RoomInfo
from rooms.domain.errors import ReservationNotFound
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.time_range import TimeRange
from rooms.infrastructure.models import Room, RoomReservationRow


def _room_info(row: Room) -> RoomInfo:
    return RoomInfo(
        id=row.pk,
        code=row.code,
        name=row.name,
        capacity_note=row.capacity_note,
        equipment=row.equipment,
        status=row.status,
    )


class DjangoRoomRepository:
    def list_all(self) -> list[RoomInfo]:
        return [_room_info(r) for r in Room.objects.all()]

    def get(self, room_id: int) -> RoomInfo | None:
        row = Room.objects.filter(pk=room_id).first()
        return _room_info(row) if row else None


def _to_domain(row: RoomReservationRow) -> RoomReservation:
    return RoomReservation(
        id=row.pk,
        user_id=row.user_id,
        room_id=row.room_id,
        requested_room_id=row.requested_room_id,
        time_range=TimeRange(row.start_at, row.end_at),
        purpose=row.purpose,
        headcount=row.headcount,
        note=row.note,
        status=ReservationStatus(row.status),
        reject_reason=row.reject_reason,
        created_by_staff=row.created_by_staff,
    )


def _fields(r: RoomReservation) -> dict:
    return {
        "user_id": r.user_id,
        "room_id": r.room_id,
        "requested_room_id": r.requested_room_id,
        "start_at": r.time_range.start,
        "end_at": r.time_range.end,
        "purpose": r.purpose,
        "headcount": r.headcount,
        "note": r.note,
        "status": r.status.value,
        "reject_reason": r.reject_reason,
        "created_by_staff": r.created_by_staff,
    }


class DjangoReservationRepository:
    def add(self, reservation: RoomReservation) -> RoomReservation:
        reservation.id = RoomReservationRow.objects.create(**_fields(reservation)).pk
        return reservation

    def get(self, reservation_id: int) -> RoomReservation | None:
        row = RoomReservationRow.objects.filter(pk=reservation_id).first()
        return _to_domain(row) if row else None

    def save(self, reservation: RoomReservation) -> None:
        RoomReservationRow.objects.filter(pk=reservation.id).update(**_fields(reservation))

    def active_between(self, start: datetime, end: datetime) -> list[RoomReservation]:
        rows = RoomReservationRow.objects.filter(
            status__in=[ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value],
            start_at__lt=end,
            end_at__gt=start,
        ).order_by("start_at", "id")
        return [_to_domain(r) for r in rows]


def _view(row: RoomReservationRow) -> ReservationView:
    return ReservationView(
        id=row.pk,
        room=_room_info(row.room),
        requested_room=_room_info(row.requested_room),
        start_at=row.start_at,
        end_at=row.end_at,
        purpose=row.purpose,
        headcount=row.headcount,
        note=row.note,
        status=row.status,
        reject_reason=row.reject_reason,
    )


class DjangoReservationReadModel:
    def _qs(self):
        return RoomReservationRow.objects.select_related("room", "requested_room")

    def get_view(self, reservation_id: int) -> ReservationView:
        row = self._qs().filter(pk=reservation_id).first()
        if row is None:
            raise ReservationNotFound("예약을 찾을 수 없습니다")
        return _view(row)

    def list_for_user(self, user_id: int) -> list[ReservationView]:
        rows = self._qs().filter(user_id=user_id).order_by("-start_at", "-id")
        return [_view(r) for r in rows]
