import pytest


@pytest.fixture(autouse=True)
def _mock_login_enabled(settings):
    settings.MOCK_LOGIN_ENABLED = True
