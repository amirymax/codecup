"""Тонкий клиент Bot API.

Нам нужны всего несколько методов, поэтому вместо python-telegram-bot здесь
обычные HTTP-запросы: у вебхука синхронный код, и асинхронный рантайм
библиотеки не дал бы ничего, кроме лишней зависимости.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramError(RuntimeError):
    """Bot API ответил ошибкой."""


class TelegramClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token if token is not None else settings.TELEGRAM_BOT_TOKEN

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def call(
        self,
        method: str,
        http_timeout: float | None = None,
        **payload: Any,
    ) -> dict[str, Any]:
        if not self.is_configured:
            raise TelegramError("TELEGRAM_BOT_TOKEN не задан.")

        url = f"{settings.TELEGRAM_API_URL}/bot{self.token}/{method}"
        response = httpx.post(
            url,
            json=payload,
            timeout=(
                http_timeout if http_timeout is not None else settings.TELEGRAM_REQUEST_TIMEOUT
            ),
        )
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(f"{method}: {data.get('description', 'неизвестная ошибка')}")
        return data.get("result", {})

    # --- методы, которыми пользуется проект ------------------------------

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self.call("sendMessage", **payload)

    def edit_message_text(self, chat_id: int, message_id: int, text: str) -> dict[str, Any]:
        return self.call(
            "editMessageText",
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode="HTML",
        )

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> dict[str, Any]:
        return self.call("answerCallbackQuery", callback_query_id=callback_query_id, text=text)

    def set_webhook(self, url: str, secret_token: str) -> dict[str, Any]:
        return self.call(
            "setWebhook",
            url=url,
            secret_token=secret_token,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )

    def delete_webhook(self) -> dict[str, Any]:
        return self.call("deleteWebhook", drop_pending_updates=True)

    def get_webhook_info(self) -> dict[str, Any]:
        return self.call("getWebhookInfo")

    def get_me(self) -> dict[str, Any]:
        return self.call("getMe")

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        """Длинный опрос: Telegram держит соединение, пока нет апдейтов.

        HTTP-таймаут берём с запасом относительно ``timeout``, иначе клиент
        разорвёт соединение раньше, чем сервер успеет ответить пустым списком.
        """
        # http_timeout — про HTTP-соединение, timeout — параметр Telegram.
        # Имена разные намеренно, иначе они перекрыли бы друг друга.
        result = self.call(
            "getUpdates",
            http_timeout=timeout + 10,
            offset=offset,
            timeout=timeout,
            allowed_updates=["message", "callback_query"],
        )
        return result if isinstance(result, list) else []


def send_message_safely(chat_id: int, text: str, **kwargs: Any) -> None:
    """Отправка, которая не роняет вебхук.

    Если Bot API недоступен, Telegram не должен получить 500 и уйти в
    бесконечные повторы — достаточно записи в лог.
    """
    try:
        TelegramClient().send_message(chat_id, text, **kwargs)
    except (TelegramError, httpx.HTTPError):
        logger.exception("Не удалось отправить сообщение в чат %s", chat_id)
