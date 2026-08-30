"""Демо-данные из макетов: тот же контест, что нарисован на главной."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.contests.models import Contest, ContestStatus
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

        for contest in created:
            self.stdout.write(f"  {contest.display_number} {contest.title} — {contest.state}")
        self.stdout.write(self.style.SUCCESS(f"Готово: {len(created)} контестов."))

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
