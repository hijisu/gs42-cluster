"""Repository 기본 틀. 구현은 각 Context의 infrastructure 계층에 둔다."""

from typing import Generic, Protocol, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class Repository(Protocol, Generic[T, ID]):
    def get(self, entity_id: ID) -> T | None: ...

    def add(self, entity: T) -> None: ...
