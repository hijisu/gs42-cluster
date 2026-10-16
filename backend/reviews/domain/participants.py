"""참여자 intra ID 파싱·검증. 순수 파이썬."""

import re

from reviews.domain.course import normalize_intra_id
from reviews.domain.errors import InvalidIntraId

_INTRA_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
_HEADER_TOKENS = {"intra_id", "intra", "login", "id"}
_SEPARATORS = re.compile(r"[,\s;]+")


def validate_intra_id(raw: str) -> str:
    intra_id = normalize_intra_id(raw)
    if not _INTRA_ID.match(intra_id):
        raise InvalidIntraId(f"올바르지 않은 intra ID입니다: {raw.strip()[:40]}")
    return intra_id


def parse_intra_ids(raw: str) -> list[str]:
    """CSV/줄바꿈/공백으로 구분된 intra ID를 정규화한다.

    첫 토큰이 헤더(intra_id 등)면 건너뛰고, 중복은 제거한다.
    """
    tokens = [t for t in _SEPARATORS.split(raw) if t]
    if tokens and tokens[0].strip().lower() in _HEADER_TOKENS:
        tokens = tokens[1:]
    seen: dict[str, None] = {}
    for token in tokens:
        seen.setdefault(validate_intra_id(token), None)
    return list(seen)
