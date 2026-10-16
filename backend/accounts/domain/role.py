"""역할 판별 규칙. 순수 파이썬(Django 의존 없음)."""

from collections.abc import Iterable
from enum import StrEnum


class Role(StrEnum):
    STUDENT = "student"
    STAFF = "staff"


def resolve_role(intra_id: str, staff_intra_ids: Iterable[str], api_staff_flag: bool) -> Role:
    """`.env`의 STAFF_INTRA_IDS가 우선이고, 42 API의 `staff?`는 보조다.

    STAFF_INTRA_IDS에 있으면 STAFF. 없을 때만 API 플래그가 true이면 STAFF.
    """
    normalized = {s.strip().lower() for s in staff_intra_ids if s.strip()}
    if intra_id.strip().lower() in normalized:
        return Role.STAFF
    return Role.STAFF if api_staff_flag else Role.STUDENT
