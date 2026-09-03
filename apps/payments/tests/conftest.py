import pytest

from apps.contests.tests.conftest import admin, client, participant  # noqa: F401
from apps.users.tests.conftest import no_telegram_calls, telegram_settings  # noqa: F401


@pytest.fixture
def admin_user():
    """Проверяющий, не подменяющий авторизацию тестового клиента."""
    from apps.users.tests.factories import AdminFactory

    return AdminFactory()
