"""예약 차단 기간(반복 일정) 유스케이스."""

from dataclasses import dataclass
from datetime import date, datetime

from rooms.application.ports import BlockRepository, ReservationRepository, RoomRepository
from rooms.domain.block import Occurrence, Repeat, RoomBlock
from rooms.domain.errors import BlockNotFound, InvalidBlock, RoomNotFound
from rooms.domain.reservation import RoomReservation
from rooms.domain.time_range import TimeRange


@dataclass(frozen=True)
class BlockCommand:
    room_id: int
    start_at: datetime
    end_at: datetime
    reason: str
    repeat: str = "none"
    weekdays: tuple[int, ...] = ()
    until: date | None = None


@dataclass(frozen=True)
class BlockResult:
    block: RoomBlock
    occurrences: list[Occurrence]
    # 차단과 겹치는 기존 활성 예약(경고용). 차단을 만들어도 기존 예약은 자동으로 바뀌지 않는다.
    conflicting: list[RoomReservation]


def _make(cmd: BlockCommand, skipped: set[date] | None = None) -> RoomBlock:
    return RoomBlock(
        room_id=cmd.room_id,
        time_range=TimeRange(cmd.start_at, cmd.end_at),
        reason=cmd.reason,
        repeat=Repeat(cmd.repeat),
        weekdays=frozenset(cmd.weekdays),
        until=cmd.until,
        skipped=set(skipped or ()),
    )


class _Base:
    def __init__(
        self, blocks: BlockRepository, reservations: ReservationRepository, rooms: RoomRepository
    ) -> None:
        self._blocks = blocks
        self._reservations = reservations
        self._rooms = rooms

    def _load(self, block_id: int) -> RoomBlock:
        block = self._blocks.get(block_id)
        if block is None:
            raise BlockNotFound("차단 일정을 찾을 수 없습니다")
        return block

    def _result(self, block: RoomBlock) -> BlockResult:
        occurrences = block.occurrences()
        conflicting: list[RoomReservation] = []
        if occurrences:
            start = min(o.time_range.start for o in occurrences)
            end = max(o.time_range.end for o in occurrences)
            active = [
                r
                for r in self._reservations.active_between(start, end)
                if r.room_id == block.room_id
            ]
            conflicting = [
                r for r in active if any(o.time_range.overlaps(r.time_range) for o in occurrences)
            ]
        return BlockResult(block, occurrences, conflicting)


class CreateBlockUseCase(_Base):
    def execute(
        self, cmd: BlockCommand, staff_id: int | None, dry_run: bool = False
    ) -> BlockResult:
        if self._rooms.get(cmd.room_id) is None:
            raise RoomNotFound("존재하지 않는 장소입니다")
        block = _make(cmd)
        if not dry_run:
            self._blocks.add(block, staff_id)
        return self._result(block)


class ListBlocksUseCase:
    def __init__(self, blocks: BlockRepository) -> None:
        self._blocks = blocks

    def execute(
        self, start: datetime, end: datetime, room_id: int | None = None
    ) -> list[tuple[RoomBlock, list[Occurrence]]]:
        window = TimeRange(start, end)
        found = self._blocks.for_rooms_between([room_id] if room_id else None, start, end)
        return [(b, occ) for b in found if (occ := b.occurrences(window))]


class UpdateBlockUseCase(_Base):
    """시리즈 전체 수정(전달한 필드만). 건너뛴 회차는 유지한다."""

    def execute(self, block_id: int, changes: dict, dry_run: bool = False) -> BlockResult:
        block = self._load(block_id)
        if "room_id" in changes and self._rooms.get(changes["room_id"]) is None:
            raise RoomNotFound("존재하지 않는 장소입니다")
        fields = dict(changes)
        if "start_at" in fields or "end_at" in fields:
            fields["time_range"] = TimeRange(
                fields.pop("start_at", block.time_range.start),
                fields.pop("end_at", block.time_range.end),
            )
        if "repeat" in fields:
            fields["repeat"] = Repeat(fields["repeat"])
        if "weekdays" in fields:
            fields["weekdays"] = frozenset(fields["weekdays"])
        updated = block.changed(**fields)
        if not updated.has_occurrences():
            raise InvalidBlock("수정 후 남는 차단 회차가 없습니다")
        if not dry_run:
            self._blocks.save(updated)
        return self._result(updated)


class DeleteBlockUseCase:
    def __init__(self, blocks: BlockRepository) -> None:
        self._blocks = blocks

    def execute(self, block_id: int) -> None:
        if not self._blocks.delete(block_id):
            raise BlockNotFound("차단 일정을 찾을 수 없습니다")


class SkipOccurrenceUseCase(_Base):
    """한 회차만 삭제한다. 마지막 회차를 지우면 시리즈 자체를 삭제한다."""

    def execute(self, block_id: int, day: date) -> None:
        block = self._load(block_id)
        block.skip(day)
        if block.has_occurrences():
            self._blocks.save(block)
        else:
            self._blocks.delete(block_id)


class UpdateOccurrenceUseCase(_Base):
    """한 회차만 수정한다: 그 회차를 시리즈에서 빼고, 수정한 내용으로 단발 차단을 새로 만든다."""

    def execute(
        self, block_id: int, day: date, changes: dict, staff_id: int | None, dry_run: bool = False
    ) -> BlockResult:
        block = self._load(block_id)
        original = block.occurrence_range(day)
        single = RoomBlock(
            room_id=changes.get("room_id", block.room_id),
            time_range=TimeRange(
                changes.get("start_at", original.start), changes.get("end_at", original.end)
            ),
            reason=changes.get("reason", block.reason),
        )
        if single.room_id != block.room_id and self._rooms.get(single.room_id) is None:
            raise RoomNotFound("존재하지 않는 장소입니다")
        if not dry_run:
            block.skip(day)
            if block.has_occurrences():
                self._blocks.save(block)
            else:
                self._blocks.delete(block_id)
            self._blocks.add(single, staff_id)
        return self._result(single)
