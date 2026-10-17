import uuid
from datetime import date, datetime, timedelta

from django.db import IntegrityError, models, transaction

from rooms.application.ports import (
    ReservationView,
    RoomInfo,
    StaffReservationRow,
    UserInfo,
)
from rooms.domain.block import Repeat, RoomBlock
from rooms.domain.errors import ReservationNotFound, RoomCodeTaken, RoomConflict
from rooms.domain.reservation import ReservationStatus, RoomReservation
from rooms.domain.rules import DEFAULT_RULES, RoomRules
from rooms.domain.time_range import TimeRange
from rooms.infrastructure.models import Room, RoomBlockRow, RoomReservationRow, RoomRulesRow


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

    def create(self, code: str | None, name: str, capacity_note: str, equipment: str) -> RoomInfo:
        order = (
            Room.objects.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0
        ) + 1
        try:
            with transaction.atomic():
                row = Room.objects.create(
                    code=code or f"room-{uuid.uuid4().hex[:8]}",
                    name=name,
                    capacity_note=capacity_note,
                    equipment=equipment,
                    sort_order=order,
                )
        except IntegrityError as exc:
            raise RoomCodeTaken(f"이미 사용 중인 장소 코드입니다: {code}") from exc
        return _room_info(row)

    def update(self, room_id: int, changes: dict) -> RoomInfo:
        Room.objects.filter(pk=room_id).update(**changes)
        return _room_info(Room.objects.get(pk=room_id))


class DjangoRulesRepository:
    def get(self) -> RoomRules:
        row = RoomRulesRow.objects.filter(pk=1).first()
        if row is None:
            return DEFAULT_RULES
        return RoomRules(
            open_hour=row.open_hour, close_hour=row.close_hour, usage_rules=tuple(row.usage_rules)
        )

    def save(self, rules: RoomRules) -> None:
        RoomRulesRow.objects.update_or_create(
            pk=1,
            defaults={
                "open_hour": rules.open_hour,
                "close_hour": rules.close_hour,
                "usage_rules": list(rules.usage_rules),
            },
        )


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
        try:
            with transaction.atomic():  # savepoint: 제약 위반 후에도 바깥 트랜잭션 유지
                RoomReservationRow.objects.filter(pk=reservation.id).update(**_fields(reservation))
        except IntegrityError as exc:  # 배타 제약: 승인된 예약과 시간이 겹침
            raise RoomConflict("이미 승인된 예약과 시간이 겹칩니다") from exc

    def lock_room(self, room_id: int) -> None:
        list(Room.objects.select_for_update().filter(pk=room_id).values_list("pk", flat=True))

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


class DjangoStaffReadModel(DjangoReservationReadModel):
    def _staff_qs(self):
        return RoomReservationRow.objects.select_related("room", "requested_room", "user")

    @staticmethod
    def _row(row: RoomReservationRow) -> StaffReservationRow:
        return StaffReservationRow(
            reservation=_to_domain(row),
            view=_view(row),
            user=UserInfo(id=row.user_id, intra_id=row.user.intra_id, name=row.user.name),
        )

    def list_for_staff(
        self, start: datetime, end: datetime, status: str | None
    ) -> list[StaffReservationRow]:
        qs = self._staff_qs().filter(start_at__lt=end, end_at__gt=start)
        if status:
            qs = qs.filter(status=status)
        return [self._row(r) for r in qs.order_by("start_at", "id")]

    def get_for_staff(self, reservation_id: int) -> StaffReservationRow:
        row = self._staff_qs().filter(pk=reservation_id).first()
        if row is None:
            raise ReservationNotFound("예약을 찾을 수 없습니다")
        return self._row(row)


def _block(row: RoomBlockRow) -> RoomBlock:
    return RoomBlock(
        id=row.pk,
        room_id=row.room_id,
        time_range=TimeRange(row.start_at, row.end_at),
        reason=row.reason,
        repeat=Repeat(row.repeat),
        weekdays=frozenset(row.weekdays),
        until=row.until,
        skipped={date.fromisoformat(d) for d in row.skipped},
    )


def _block_fields(block: RoomBlock) -> dict:
    return {
        "room_id": block.room_id,
        "start_at": block.time_range.start,
        "end_at": block.time_range.end,
        "reason": block.reason,
        "repeat": block.repeat.value,
        "weekdays": sorted(block.weekdays),
        "until": block.until,
        "skipped": sorted(d.isoformat() for d in block.skipped),
    }


class DjangoBlockRepository:
    def add(self, block: RoomBlock, created_by: int | None) -> RoomBlock:
        block.id = RoomBlockRow.objects.create(created_by_id=created_by, **_block_fields(block)).pk
        return block

    def get(self, block_id: int) -> RoomBlock | None:
        row = RoomBlockRow.objects.filter(pk=block_id).first()
        return _block(row) if row else None

    def save(self, block: RoomBlock) -> None:
        RoomBlockRow.objects.filter(pk=block.id).update(**_block_fields(block))

    def delete(self, block_id: int) -> bool:
        deleted, _ = RoomBlockRow.objects.filter(pk=block_id).delete()
        return bool(deleted)

    def for_rooms_between(
        self, room_ids: list[int] | None, start: datetime, end: datetime
    ) -> list[RoomBlock]:
        # 첫 회차가 구간 끝 이전에 시작하고, 반복이 없거나 종료일이 구간 시작 날짜 이후인 시리즈
        rows = RoomBlockRow.objects.filter(start_at__lt=end)
        if room_ids is not None:
            rows = rows.filter(room_id__in=room_ids)
        recurring_until = (start - timedelta(days=1)).date()
        rows = rows.filter(
            models.Q(repeat="none", end_at__gt=start)
            | (~models.Q(repeat="none") & models.Q(until__gte=recurring_until))
        )
        return [_block(r) for r in rows]
