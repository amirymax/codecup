"""Тексты бота. Всё на русском — как и остальной интерфейс."""

WELCOME = (
    "👋 Привет! Это бот <b>CodeCup.tech</b>.\n\n"
    "Чтобы войти на сайт, откройте страницу входа и нажмите "
    "«Войти через Telegram»."
)

CONFIRM_PROMPT = (
    "🔐 Подтвердите вход на <b>CodeCup.tech</b>.\n\nЕсли это были не вы — просто нажмите «Отмена»."
)

CONFIRM_BUTTON = "✅ Подтвердить вход"
CANCEL_BUTTON = "✖️ Отмена"

LINK_EXPIRED = "⏳ Ссылка для входа устарела.\n\nВернитесь на сайт и попробуйте войти ещё раз."

LOGIN_CONFIRMED = "✅ Вход подтверждён. Можете вернуться на сайт — вы уже авторизованы."

LOGIN_CANCELLED = "✖️ Вход отменён."

ALREADY_HANDLED = "Эта ссылка уже использована."

CALLBACK_CONFIRMED = "Готово"
CALLBACK_CANCELLED = "Отменено"
CALLBACK_EXPIRED = "Ссылка устарела"


def confirm_keyboard(nonce: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": CONFIRM_BUTTON, "callback_data": f"confirm:{nonce}"}],
            [{"text": CANCEL_BUTTON, "callback_data": f"cancel:{nonce}"}],
        ]
    }
