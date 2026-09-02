"""Сбор посещаемости и сводка для админки."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.analytics.models import Event

pytestmark = pytest.mark.django_db

TRACK = "track-event"
SUMMARY = "admin-analytics"


def _visit(client: APIClient, path="/", name="pageview", ip="10.0.0.1", agent="Firefox"):
    return client.post(
        reverse(TRACK),
        {"name": name, "path": path},
        format="json",
        REMOTE_ADDR=ip,
        HTTP_USER_AGENT=agent,
    )


# --- сбор ------------------------------------------------------------------


def test_guest_visit_is_recorded(client: APIClient) -> None:
    """Гости — большая часть трафика, ради них статистика и нужна."""
    assert _visit(client, "/contests/one").status_code == 204

    event = Event.objects.get()
    assert event.name == "pageview"
    assert event.path == "/contests/one"
    assert event.user is None


def test_ip_address_is_not_stored(client: APIClient) -> None:
    _visit(client, ip="203.0.113.7")

    event = Event.objects.get()
    assert "203.0.113.7" not in event.visitor
    assert len(event.visitor) == 32


def test_query_string_is_dropped_from_the_path(client: APIClient) -> None:
    """В query попадают персональные данные, а для статистики он не нужен."""
    _visit(client, "/login?next=/profile&token=secret")

    assert Event.objects.get().path == "/login"


def test_event_name_must_look_like_a_name(client: APIClient) -> None:
    assert _visit(client, name="<script>").status_code == 400
    assert Event.objects.count() == 0


def test_a_logged_in_visit_remembers_who_it_was(client: APIClient, participant) -> None:
    _visit(client)

    assert Event.objects.get().user == participant


# --- сводка ----------------------------------------------------------------


def test_summary_counts_views_and_unique_visitors(client: APIClient, admin) -> None:
    _visit(client, "/", ip="10.0.0.1")
    _visit(client, "/", ip="10.0.0.1")
    _visit(client, "/", ip="10.0.0.2")

    body = client.get(reverse(SUMMARY)).json()

    assert body["views"] == 3
    assert body["visitors"] == 2


def test_same_address_with_another_browser_is_another_visitor(client: APIClient, admin) -> None:
    _visit(client, ip="10.0.0.1", agent="Firefox")
    _visit(client, ip="10.0.0.1", agent="Safari")

    assert client.get(reverse(SUMMARY)).json()["visitors"] == 2


def test_summary_breaks_views_down_by_page(client: APIClient, admin) -> None:
    _visit(client, "/contests/one")
    _visit(client, "/contests/one", ip="10.0.0.2")
    _visit(client, "/")

    pages = {row["path"]: row for row in client.get(reverse(SUMMARY)).json()["pages"]}

    assert pages["/contests/one"]["views"] == 2
    assert pages["/contests/one"]["visitors"] == 2
    assert pages["/"]["views"] == 1


def test_button_clicks_are_counted_separately_from_views(client: APIClient, admin) -> None:
    _visit(client, "/contests/one")
    _visit(client, "/contests/one", name="participate_click")
    _visit(client, "/contests/one", name="participate_click", ip="10.0.0.2")

    body = client.get(reverse(SUMMARY)).json()

    assert body["views"] == 1, "клики не должны попадать в просмотры"
    clicks = next(row for row in body["events"] if row["name"] == "participate_click")
    assert clicks["count"] == 2
    assert clicks["visitors"] == 2


def test_summary_has_a_point_for_each_day_with_traffic(client: APIClient, admin) -> None:
    _visit(client)
    _visit(client, ip="10.0.0.2")

    daily = client.get(reverse(SUMMARY)).json()["daily"]

    assert len(daily) == 1
    assert daily[0]["views"] == 2
    assert daily[0]["visitors"] == 2


def test_window_can_be_narrowed_and_nonsense_is_ignored(client: APIClient, admin) -> None:
    assert client.get(reverse(SUMMARY), {"days": "7"}).json()["days"] == 7
    assert client.get(reverse(SUMMARY), {"days": "сколько"}).json()["days"] == 30
    assert client.get(reverse(SUMMARY), {"days": "-5"}).json()["days"] == 1


def test_participant_cannot_read_the_summary(client: APIClient, participant) -> None:
    assert client.get(reverse(SUMMARY)).status_code == 403


def test_guest_cannot_read_the_summary(client: APIClient) -> None:
    assert client.get(reverse(SUMMARY)).status_code == 401
