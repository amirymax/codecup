from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.users.cookies import issue_tokens
from apps.users.tests.factories import AdminFactory, UserFactory


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def _authenticate(client: APIClient, user):
    from django.conf import settings

    access, refresh = issue_tokens(user)
    client.cookies[settings.AUTH_COOKIE_ACCESS_NAME] = access
    client.cookies[settings.AUTH_COOKIE_REFRESH_NAME] = refresh
    return user


@pytest.fixture
def participant(client: APIClient):
    return _authenticate(client, UserFactory())


@pytest.fixture
def admin(client: APIClient):
    return _authenticate(client, AdminFactory())
