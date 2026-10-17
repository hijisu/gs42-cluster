"""Makefile(make dev / run / demoreset)과 docs/BUILD.md 설명의 정합성."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
BUILD_MD = ROOT / "docs" / "BUILD.md"

if not MAKEFILE.is_file() or not BUILD_MD.is_file():
    pytest.skip(
        "저장소 루트의 Makefile/docs 가 보이지 않는 환경(컨테이너)", allow_module_level=True
    )


def recipe(target: str) -> str:
    text = MAKEFILE.read_text(encoding="utf-8")
    match = re.search(rf"^{target}:.*\n((?:\t.*\n?)+)", text, re.MULTILINE)
    assert match, f"Makefile 에 {target} 목표가 없습니다"
    return match.group(1)


def test_dev_seeds_demo_and_imports_books_without_reset():
    body = recipe("dev")
    assert "seed_demo" in body and "import_books" in body
    assert "--reset" not in body


def test_run_is_production_and_only_imports_books():
    body = recipe("run")
    assert "$(PROD)" in body
    definition = re.search(r"^PROD\s*:=.*$", MAKEFILE.read_text(encoding="utf-8"), re.MULTILINE)
    assert definition and "docker-compose.prod.yml" in definition.group(0)
    assert "$(PROJECT)-prod" in definition.group(0)
    assert "import_books" in body
    assert "seed_demo" not in body


def test_demoreset_resets_demo_data():
    assert "seed_demo --reset" in recipe("demoreset")


def test_build_md_documents_every_make_target():
    text = BUILD_MD.read_text(encoding="utf-8")
    for command in ("make dev", "make run", "make demoreset"):
        assert command in text, f"docs/BUILD.md 에 `{command}` 설명이 없습니다"
