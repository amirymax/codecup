"""Демо-данные из макетов: тот же контест, что нарисован на главной."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.contests.models import Contest, ContestStatus
from apps.submissions.models import Submission, SubmissionStatus
from apps.users.models import User

FEATURED = {
    "title": "Создайте инструмент для разработчиков на базе ИИ",
    "description": (
        "Соберите рабочий инструмент для разработчиков, который осмысленно "
        "использует ИИ — CLI, расширение для IDE, агент, бот для код-ревью, "
        "что угодно, что помогает разработчикам работать быстрее. "
        "Соло-участники приветствуются; ИИ-напарники полностью разрешены."
    ),
    "requirements": [
        "Публичный репозиторий GitHub с понятным README",
        "Живая, публично доступная демо-ссылка",
        "Короткое (до 3 минут) демо-видео",
        "Осмысленно использует ИИ в продукте",
    ],
    "prize_pool": Decimal("5000.00"),
    "is_featured": True,
    "status": ContestStatus.PUBLISHED,
}

ENDED = {
    "title": "Соберите CLI за 48 часов",
    "description": "Инструмент командной строки, написанный за выходные.",
    "requirements": ["Публичный репозиторий GitHub", "Инструкция по установке"],
    "prize_pool": Decimal("2000.00"),
    "is_featured": False,
    "status": ContestStatus.PUBLISHED,
}

DRAFT = {
    "title": "Уик-энд открытого кода",
    "description": "Черновик следующего контеста.",
    "requirements": ["Вклад в существующий open-source проект"],
    "prize_pool": Decimal("1000.00"),
    "is_featured": False,
    "status": ContestStatus.DRAFT,
}


class Command(BaseCommand):
    help = "Заполнить базу демонстрационными контестами из макетов."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-telegram-id",
            type=int,
            default=1,
            help="Telegram ID для демо-администратора.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._demo_admin(options["admin_telegram_id"])
        now = timezone.now()

        created = [
            self._contest(FEATURED, deadline=now + timedelta(days=4, hours=12), author=admin),
            self._contest(ENDED, deadline=now - timedelta(days=30), author=admin),
            self._contest(DRAFT, deadline=now + timedelta(days=60), author=admin),
        ]

        submissions = self._submissions(created[0])

        for contest in created:
            self.stdout.write(f"  {contest.display_number} {contest.title} — {contest.state}")
        self.stdout.write(
            self.style.SUCCESS(f"Готово: {len(created)} контестов, {len(submissions)} заявок.")
        )

    def _demo_admin(self, telegram_id: int) -> User:
        admin, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={"username": "demo_admin", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_unusable_password()
            admin.save(update_fields=["password"])
            self.stdout.write("Создан демо-администратор demo_admin.")
        return admin

    def _contest(self, data: dict, *, deadline, author: User) -> Contest:
        contest, _ = Contest.objects.update_or_create(
            title=data["title"],
            defaults={**data, "deadline": deadline, "created_by": author},
        )
        return contest

    def _submissions(self, contest: Contest) -> list[Submission]:
        """Четыре заявки из макета админ-панели — по одной на каждый статус."""
        people = [
            ("sarah_dev", "ai-lint-agent", SubmissionStatus.SUBMITTED, None, False),
            ("max_builds", "promptql", SubmissionStatus.REVIEWED, 78, False),
            ("ana_codes", "devcopilot-cli", SubmissionStatus.DRAFT, None, False),
            ("jordan_k", "aitest-runner", SubmissionStatus.REVIEWED, 94, True),
        ]

        created = []
        for index, (username, repo, status, score, is_winner) in enumerate(people, start=10):
            user, _ = User.objects.get_or_create(
                telegram_id=index,
                defaults={"username": username, "telegram_username": username},
            )
            submission, _ = Submission.objects.update_or_create(
                contest=contest,
                user=user,
                defaults={
                    "github_url": f"https://github.com/{username}/{repo}",
                    "live_url": f"https://{repo}.vercel.app",
                    "video_url": "https://youtube.com/watch?v=demo",
                    "description": "Инструмент для разработчиков, использующий ИИ.",
                    "status": status,
                    "score": score,
                    "is_winner": is_winner,
                    "submitted_at": (None if status == SubmissionStatus.DRAFT else timezone.now()),
                },
            )
            created.append(submission)
        return created
