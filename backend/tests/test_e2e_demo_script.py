"""scripts/e2e_demo.py(시연 핵심 시나리오 2개)를 실제 HTTP 서버(live_server)에서 2회 실행한다."""

import importlib.util
import os
from pathlib import Path

import pytest
from django.core.management import call_command

# 트랜잭션 테스트는 끝날 때 DB 를 비우므로 마이그레이션이 넣은 장소·면담 유형을 복원하게 한다.
pytestmark = pytest.mark.django_db(transaction=True, serialized_rollback=True)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "e2e_demo.py"


@pytest.fixture(scope="module")
def e2e():
    if not SCRIPT.is_file():
        if os.environ.get("CI"):
            pytest.fail(f"CI에서 {SCRIPT} 를 찾을 수 없습니다")
        pytest.skip("저장소 루트의 scripts/ 가 보이지 않는 환경(컨테이너)")
    spec = importlib.util.spec_from_file_location("e2e_demo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def demo_stack(settings, live_server):
    settings.DEBUG = True
    settings.MOCK_LOGIN_ENABLED = True
    call_command("seed_demo", "--reset", days=10, verbosity=0)
    return live_server.url


def test_both_scenarios_pass_twice_in_a_row_and_leave_no_residue(e2e, demo_stack):
    from meetings.infrastructure.models import MeetingRequestRow
    from rooms.infrastructure.models import RoomReservationRow

    for number in (1, 2):
        ok, lines = e2e.run_once(demo_stack, number, check_spa=False)
        assert ok, "\n".join(lines)
    # 정리 단계가 취소해서 활성 신청이 남지 않는다
    assert (
        not MeetingRequestRow.objects.exclude(status="canceled")
        .filter(student__intra_id="student")
        .exists()
    )
    assert (
        not RoomReservationRow.objects.exclude(status="canceled")
        .filter(user__intra_id="student")
        .exists()
    )


def test_script_reports_failure_and_exit_code_when_demo_data_is_missing(e2e, settings, live_server):
    settings.DEBUG = True
    settings.MOCK_LOGIN_ENABLED = True  # 시드를 돌리지 않아 면담 가능 시간이 없다
    code = e2e.main(["--base", live_server.url, "--skip-spa"])
    assert code == 1


def test_script_explains_when_mock_login_is_off(e2e, settings, live_server):
    settings.MOCK_LOGIN_ENABLED = False  # 운영 모드
    ok, lines = e2e.run_once(live_server.url, 1, check_spa=False)
    assert not ok and "모의 로그인이 꺼져 있습니다" in "\n".join(lines)
