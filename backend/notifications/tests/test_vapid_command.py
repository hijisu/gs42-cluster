import io

from django.core.management import call_command

from notifications.infrastructure.vapid import public_key_of


def test_generate_vapid_keys_prints_a_usable_pair_without_storing_anything():
    out, err = io.StringIO(), io.StringIO()
    call_command("generate_vapid_keys", stdout=out, stderr=err)
    lines = dict(line.split("=", 1) for line in out.getvalue().strip().splitlines())
    assert set(lines) == {"VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY"}
    assert public_key_of(lines["VAPID_PRIVATE_KEY"]) == lines["VAPID_PUBLIC_KEY"]
    assert "비밀값" in err.getvalue()  # 개인키 취급 주의 안내는 stderr 로
    assert lines["VAPID_PRIVATE_KEY"] not in err.getvalue()  # 개인키가 안내문에 섞이지 않는다
