from __future__ import annotations

from datetime import timedelta

import factory
from django.utils import timezone

from apps.contests.tests.factories import ContestFactory
from apps.submissions.models import Submission, SubmissionStatus
from apps.users.tests.factories import UserFactory


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission
        skip_postgeneration_save = True

    contest = factory.SubFactory(ContestFactory)
    user = factory.SubFactory(UserFactory)
    github_url = factory.Sequence(lambda n: f"https://github.com/dev{n}/project{n}")
    live_url = factory.Sequence(lambda n: f"https://project{n}.vercel.app")
    description = "Инструмент для разработчиков на базе ИИ."
    status = SubmissionStatus.DRAFT


class SubmittedFactory(SubmissionFactory):
    status = SubmissionStatus.SUBMITTED
    # Возрастающая последовательность, а не случайная дата: порядок очереди
    # проверки должен быть предсказуемым в тестах навигации.
    submitted_at = factory.Sequence(
        lambda n: timezone.now() - timedelta(days=30) + timedelta(minutes=n)
    )
