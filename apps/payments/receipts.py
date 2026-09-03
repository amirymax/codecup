"""Выдача чеков об оплате.

Чек — это скриншот перевода: там номер карты, имя и сумма. В открытый доступ
такое класть нельзя, поэтому media наружу не отдаётся вовсе, а файл выдаётся
только после проверки прав.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, HttpResponse

from .models import EntryPayment


def receipt_response(payment: EntryPayment) -> HttpResponse:
    """Ответ с чеком: через nginx в проде и напрямую в разработке."""
    filename = Path(payment.receipt.name).name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    if settings.USE_X_ACCEL_REDIRECT:
        # Тело пустое: файл подставит nginx, а Django остаётся проверка прав.
        response = HttpResponse(content_type=content_type)
        location = settings.MEDIA_INTERNAL_LOCATION + quote(payment.receipt.name)
        response["X-Accel-Redirect"] = location
    else:
        response = FileResponse(payment.receipt.open("rb"), content_type=content_type)

    # inline: чек чаще смотрят, чем скачивают.
    response["Content-Disposition"] = f'inline; filename="{quote(filename)}"'
    return response
