"""Выдать права администратора существующему пользователю."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.users.models import User


class Command(BaseCommand):
    help = (
        "Сделать пользователя администратором. Найти его можно по "
        "@username в Telegram или по числовому Telegram ID."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--telegram-username", help="Без символа @, например AmiriCode")
        group.add_argument("--telegram-id", type=int, help="Числовой Telegram ID")
        parser.add_argument(
            "--revoke",
            action="store_true",
            help="Наоборот, снять права администратора.",
        )

    def handle(self, *args, **options):
        user = self._find(options)
        grant = not options["revoke"]

        user.is_staff = grant
        user.is_superuser = grant
        user.save(update_fields=["is_staff", "is_superuser", "updated_at"])

        action = "теперь администратор" if grant else "больше не администратор"
        self.stdout.write(self.style.SUCCESS(f"{user.username} ({user.telegram_id}) — {action}."))

    def _find(self, options) -> User:
        if options["telegram_id"] is not None:
            user = User.objects.filter(telegram_id=options["telegram_id"]).first()
            missing = f"Telegram ID {options['telegram_id']}"
        else:
            username = options["telegram_username"].lstrip("@")
            user = User.objects.filter(telegram_username__iexact=username).first()
            missing = f"@{username}"

        if user is None:
            raise CommandError(
                f"Пользователь {missing} не найден.\n"
                "Аккаунт создаётся при первом входе — откройте сайт, войдите "
                "через Telegram, затем повторите команду."
            )
        return user
