"""운영(DJANGO_DEBUG=false) 설정 가드. 설정은 import 시점에 평가되어 별도 프로세스에서 확인한다."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
PROBE = (
    "from django.conf import settings as s;"
    "print(s.DEBUG, s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.MOCK_LOGIN_ENABLED)"
)


def run(**env):
    # 저장소 루트의 .env 가 값을 채우지 않도록 필요한 키를 모두 명시한다.
    base = {
        "PATH": os.environ.get("PATH", ""),
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "a-real-secret-for-tests",
    }
    return subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=BACKEND,
        env={**base, **env},
        capture_output=True,
        text=True,
    )


def test_production_defaults_are_secure_and_disable_mock_login():
    result = run()
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "True", "True", "False"]


@pytest.mark.parametrize("key", ["change-me", "insecure-dev-only-key"])
def test_production_refuses_example_secret_keys(key):
    result = run(DJANGO_SECRET_KEY=key)
    assert result.returncode != 0 and "example value" in result.stderr


def test_production_requires_a_secret_key():
    result = run(DJANGO_SECRET_KEY="")
    assert result.returncode != 0 and "must be set" in result.stderr


def test_debug_mode_still_allows_the_example_key():
    result = run(DJANGO_DEBUG="true", DJANGO_SECRET_KEY="change-me")
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["True", "False", "False", "True"]


def test_cookie_secure_can_be_turned_off_only_explicitly():
    result = run(DJANGO_COOKIE_SECURE="false")
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "False", "False", "False"]
