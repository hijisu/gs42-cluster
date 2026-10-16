"""운영(DJANGO_DEBUG=false)에서는 모의 로그인이 꺼진다."""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def _flag(debug: str) -> str:
    env = {
        **os.environ,
        "DJANGO_DEBUG": debug,
        "DJANGO_SECRET_KEY": "test-key",
        "DJANGO_SETTINGS_MODULE": "config.settings",
    }
    code = "from django.conf import settings; print(settings.MOCK_LOGIN_ENABLED)"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND, env=env, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_mock_login_enabled_only_in_debug():
    assert _flag("true") == "True"
    assert _flag("false") == "False"
