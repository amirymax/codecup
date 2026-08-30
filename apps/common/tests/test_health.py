import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_health_reports_ok_when_database_is_reachable(client: APIClient) -> None:
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_health_reports_503_when_database_is_unreachable(client: APIClient, monkeypatch) -> None:
    from apps.common.views import HealthView

    monkeypatch.setattr(HealthView, "_database_ok", staticmethod(lambda: False))

    response = client.get(reverse("health"))

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_openapi_schema_is_generated(client: APIClient) -> None:
    response = client.get(reverse("schema"))

    assert response.status_code == 200


def test_unknown_api_path_returns_the_json_error_envelope(client: APIClient) -> None:
    response = client.get("/api/does-not-exist/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_unknown_non_api_path_is_left_to_django(client: APIClient) -> None:
    assert client.get("/does-not-exist/").status_code == 404
