"""Слаги для русских названий.

``django.utils.text.slugify`` выбрасывает кириллицу целиком, а
``allow_unicode=True`` даёт в адресной строке процентную кашу при копировании.
Поэтому названия транслитерируются в латиницу.
"""

from __future__ import annotations

from django.utils.text import slugify

TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    # таджикские буквы
    "ғ": "gh",
    "ӣ": "i",
    "қ": "q",
    "ӯ": "u",
    "ҳ": "h",
    "ҷ": "j",
}


def transliterate(value: str) -> str:
    result = []
    for char in value:
        replacement = TRANSLIT.get(char.lower())
        if replacement is None:
            result.append(char)
        else:
            result.append(replacement.title() if char.isupper() else replacement)
    return "".join(result)


def slugify_ru(value: str) -> str:
    return slugify(transliterate(value))


def unique_slug(model, value: str, *, fallback: str, exclude_pk=None) -> str:
    """Подбирает свободный слаг, добавляя -2, -3 … при совпадении."""
    base = slugify_ru(value) or fallback
    candidate, suffix = base, 1

    queryset = model.objects.all()
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)

    while queryset.filter(slug=candidate).exists():
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate
