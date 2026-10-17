"""`.env.example` 과 docs/BUILD.md 의 정합성 (AGENTS.md: 새 환경변수는 둘 다에 적는다)."""

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
KEY_LINE = re.compile(r"^#?\s*([A-Z][A-Z0-9_]+)=(.*)$")
SECRET_WORDS = ("SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY")
PLACEHOLDERS = {"", "change-me"}


@pytest.fixture(autouse=True)
def _repo_root_files():
    """개발용 컨테이너에는 ./backend 만 마운트되어 저장소 루트 파일이 없다 → 건너뛴다.

    CI(환경변수 CI 설정)에서는 전체 체크아웃이므로 파일이 없으면 건너뛰지 않고 실패시킨다.
    """
    missing = [p for p in (ROOT / ".env.example", ROOT / "docs" / "BUILD.md") if not p.is_file()]
    if missing:
        if os.environ.get("CI"):
            pytest.fail(f"CI에서 저장소 루트 파일을 찾을 수 없습니다: {missing}")
        pytest.skip("저장소 루트의 .env.example/docs 가 보이지 않는 환경(컨테이너)")


def example_entries() -> list[tuple[str, str]]:
    entries = []
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        match = KEY_LINE.match(line.strip())
        if match:
            entries.append((match.group(1), match.group(2).strip()))
    return entries


def test_example_file_is_parsed():
    keys = {k for k, _ in example_entries()}
    assert {"DJANGO_SECRET_KEY", "POSTGRES_DB", "FORTYTWO_UID", "STAFF_INTRA_IDS"} <= keys


def test_every_env_example_key_is_documented_in_build_md():
    doc = (ROOT / "docs" / "BUILD.md").read_text(encoding="utf-8")
    wildcards = set(re.findall(r"`([A-Z][A-Z0-9_]*_)\*`", doc))  # 예: `POSTGRES_*`, `VAPID_*`
    missing = [
        key
        for key, _ in example_entries()
        if key not in doc and not any(key.startswith(prefix) for prefix in wildcards)
    ]
    assert not missing, f"docs/BUILD.md 에 설명이 없는 .env.example 키: {missing}"


def test_env_example_contains_no_real_secrets():
    """비밀값 칸은 비우거나 예시 값(change-me)만 허용한다. 실수로 실제 값을 커밋하지 않게 한다."""
    leaked = [
        key
        for key, value in example_entries()
        if any(word in key for word in SECRET_WORDS) and value not in PLACEHOLDERS
    ]
    assert not leaked, f".env.example 에 값이 들어 있는 비밀 키: {leaked}"
