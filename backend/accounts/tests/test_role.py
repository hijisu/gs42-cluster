import pytest

from accounts.domain.role import Role, resolve_role


def test_staff_list_wins_over_api_flag():
    assert resolve_role("alice", ["alice"], api_staff_flag=False) == Role.STAFF


def test_api_flag_is_fallback():
    assert resolve_role("bob", [], api_staff_flag=True) == Role.STAFF


def test_default_is_student():
    assert resolve_role("carol", ["alice"], api_staff_flag=False) == Role.STUDENT


@pytest.mark.parametrize("login", ["Alice", " alice "])
def test_staff_match_ignores_case_and_whitespace(login):
    assert resolve_role(login, ["alice"], False) == Role.STAFF
