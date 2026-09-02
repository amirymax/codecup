"""Проверка присланных заявок. Ставится в cron раз в несколько минут."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.screening.models import ScreeningStatus, SubmissionScreening
from apps.screening.service import screen_submission
from apps.submissions.models import Submission


class Command(BaseCommand):
    help = "Проверить присланные репозитории на утечки и соответствие требованиям."

    def add_arguments(self, parser):
        parser.add_argument("--submission", type=int, help="Проверить одну заявку по id.")
        parser.add_argument(
            "--recheck",
            action="store_true",
            help="Проверить заново, даже если проверка уже была.",
        )
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **options):
        for submission in self._queue(options):
            self.stdout.write(f"Проверяю #{submission.id} {submission.github_url}")
            screening = screen_submission(submission)

            if screening.status == ScreeningStatus.FAILED:
                self.stdout.write(self.style.ERROR(f"  не удалось: {screening.error}"))
                continue

            count = len(screening.findings)
            style = self.style.WARNING if count else self.style.SUCCESS
            self.stdout.write(style(f"  находок: {count} (файлов: {screening.files_scanned})"))

    def _queue(self, options):
        queryset = Submission.objects.counted().select_related("contest")

        if options["submission"]:
            return queryset.filter(pk=options["submission"])

        if not options["recheck"]:
            # Уже проверенные пропускаем, кроме сорвавшихся.
            done = SubmissionScreening.objects.filter(status=ScreeningStatus.DONE).values_list(
                "submission_id", flat=True
            )
            queryset = queryset.exclude(pk__in=done)

        return queryset[: options["limit"]]
