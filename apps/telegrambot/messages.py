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


# --- оплата участия --------------------------------------------------------

ASK_FOR_RECEIPT = (
    "💳 Пришлите, пожалуйста, чек об оплате взноса.\n\n"
    "Подойдёт скриншот или PDF — отправьте его сюда одним сообщением."
)

RECEIPT_RECEIVED = "✅ Чек получен и отправлен на проверку. Мы сообщим о решении."

RECEIPT_NOT_EXPECTED = (
    "Сейчас я не жду от вас чек.\n\nОткройте страницу контеста на сайте и нажмите «Участвовать»."
)

RECEIPT_WRONG_FORMAT = "Нужен скриншот или PDF. Пришлите файл ещё раз."

ADMIN_DECISION_ACCEPTED = "Принято"
ADMIN_DECISION_REJECTED = "Отклонено"


def receipt_for_admin(payment) -> str:
    who = payment.user.telegram_username or payment.user.username
    return (
        f"🧾 <b>Новый чек</b>\n\n"
        f"Участник: @{who}\n"
        f"Контест: {payment.contest.title}\n"
        f"Сумма: {payment.amount} {payment.currency}"
    )


def decision_keyboard(payment_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Принять", "callback_data": f"pay_ok:{payment_id}"},
                {"text": "✖️ Отклонить", "callback_data": f"pay_no:{payment_id}"},
            ]
        ]
    }


def payment_accepted(payment) -> str:
    return (
        f"✅ Взнос за «{payment.contest.title}» принят.\n\nТеперь можно отправить решение на сайте."
    )


def payment_rejected(payment) -> str:
    reason = f"\n\nПричина: {payment.rejection_reason}" if payment.rejection_reason else ""
    return f"✖️ Чек за «{payment.contest.title}» отклонён.{reason}\n\nМожно прислать новый."
