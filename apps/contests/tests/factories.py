from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from apps.contests.models import Contest, ContestStatus


class ContestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contest
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Контест номер {n}")
    description = "Соберите что-нибудь полезное."
    requirements = factory.LazyFunction(
        lambda: ["Публичный репозиторий GitHub", "Живая демо-ссылка"]
    )
    prize_pool = Decimal("5000.00")
    status = ContestStatus.PUBLISHED
    deadline = factory.LazyFunction(lambda: timezone.now() + timedelta(days=4))


class DraftContestFactory(ContestFactory):
    status = ContestStatus.DRAFT


class EndedContestFactory(ContestFactory):
    deadline = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
