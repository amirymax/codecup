import pytest
from rest_framework.exceptions import NotFound, ValidationError

from apps.common.exceptions import DomainError, api_exception_handler


def _handle(exc: Exception) -> dict:
    response = api_exception_handler(exc, {})
    assert response is not None
    return response.data["error"]


def test_not_found_is_wrapped_with_a_machine_code() -> None:
    error = _handle(NotFound("Контест не найден."))

    assert error["code"] == "not_found"
    assert error["message"] == "Контест не найден."


def test_validation_errors_are_returned_per_field() -> None:
    error = _handle(ValidationError({"github_url": ["Ссылка должна вести на github.com."]}))

    assert error["code"] == "invalid"
    assert error["details"]["github_url"] == ["Ссылка должна вести на github.com."]


def test_domain_error_carries_its_own_code_and_details() -> None:
    error = _handle(DomainError("Приём заявок закрыт.", code="contest_closed", slug="ai-dev-tool"))

    assert error["code"] == "contest_closed"
    assert error["message"] == "Приём заявок закрыт."
    assert error["details"]["slug"] == "ai-dev-tool"


def test_non_api_exceptions_are_not_swallowed() -> None:
    assert api_exception_handler(RuntimeError("boom"), {}) is None


@pytest.mark.parametrize("status_code", [409])
def test_domain_error_defaults_to_conflict(status_code: int) -> None:
    assert DomainError.status_code == status_code


def test_django_http404_keeps_the_not_found_code() -> None:
    """get_object_or_404 бросает Http404, а не NotFound — код не должен теряться."""
    from django.http import Http404

    assert _handle(Http404("нет такого"))["code"] == "not_found"


def test_django_permission_denied_keeps_its_code() -> None:
    from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

    assert _handle(DjangoPermissionDenied())["code"] == "permission_denied"


def test_http404_message_is_russian_and_hides_the_model_name() -> None:
    from django.http import Http404

    error = _handle(Http404("No Contest matches the given query."))

    assert "Contest" not in error["message"]
    assert error["message"] == "Страница не найдена."
