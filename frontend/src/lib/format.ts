/** Форматирование чисел и дат — везде одинаковое. */

const MONTHS_SHORT = [
  "янв", "фев", "мар", "апр", "мая", "июн",
  "июл", "авг", "сен", "окт", "ноя", "дек",
];

/** Именительный падеж — для строк вида «август 2026». */
const MONTHS_NOMINATIVE = [
  "январь", "февраль", "март", "апрель", "май", "июнь",
  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
];

/** Символ ставится перед суммой только у доллара — так принято для $. */
const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  TJS: "смн",
  RUB: "₽",
};

/** «$5 000», «5 000 смн», «5 000 ₽». */
export function formatMoney(amount: string | number, currency = "USD"): string {
  const value = typeof amount === "string" ? Number.parseFloat(amount) : amount;
  const formatted = new Intl.NumberFormat("ru-RU").format(Math.round(value));
  const symbol = CURRENCY_SYMBOLS[currency] ?? currency;

  return currency === "USD" ? `${symbol}${formatted}` : `${formatted} ${symbol}`;
}

export const CURRENCIES = [
  { code: "USD", label: "Доллар США ($)" },
  { code: "TJS", label: "Сомони (смн)" },
  { code: "RUB", label: "Рубль (₽)" },
] as const;

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("ru-RU").format(value);
}

/** «12 июл» — короткая дата дедлайна. */
export function formatShortDate(iso: string): string {
  const date = new Date(iso);
  return `${date.getDate()} ${MONTHS_SHORT[date.getMonth()]}`;
}

/**
 * «июнь 2026» — для строки «Присоединился через Telegram».
 *
 * Именительный падеж берётся из отдельного списка: получить его из
 * родительного отбрасыванием окончания нельзя — «августа» так не
 * превращается в «август».
 */
export function formatMonthYear(iso: string): string {
  const date = new Date(iso);
  return `${MONTHS_NOMINATIVE[date.getMonth()]} ${date.getFullYear()}`;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return `${date.getDate()} ${MONTHS_SHORT[date.getMonth()]} ${date.getFullYear()}`;
}

/**
 * «2 дня назад» — русские окончания зависят от числа,
 * поэтому Intl.RelativeTimeFormat, а не ручная склейка.
 */
export function formatRelative(iso: string | null): string {
  if (!iso) return "—";

  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  const formatter = new Intl.RelativeTimeFormat("ru", { numeric: "auto" });

  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["year", 31_536_000],
    ["month", 2_592_000],
    ["day", 86_400],
    ["hour", 3_600],
    ["minute", 60],
  ];

  for (const [unit, size] of units) {
    if (seconds >= size) {
      return formatter.format(-Math.floor(seconds / size), unit);
    }
  }
  return "только что";
}

/** «1 балл», «3 балла», «85 баллов» — окончание зависит от числа. */
const SCORE_FORMS: Record<string, string> = {
  one: "балл",
  few: "балла",
  many: "баллов",
  other: "балла",
};

export function formatScore(value: number): string {
  const form = new Intl.PluralRules("ru").select(value);
  return `${value} ${SCORE_FORMS[form] ?? SCORE_FORMS.many}`;
}

/** Разбивает оставшиеся секунды на части обратного отсчёта. */
export function splitDuration(totalSeconds: number) {
  const safe = Math.max(0, totalSeconds);
  return {
    days: Math.floor(safe / 86_400),
    hours: Math.floor((safe % 86_400) / 3_600),
    minutes: Math.floor((safe % 3_600) / 60),
    seconds: safe % 60,
  };
}

export const pad = (value: number): string => String(value).padStart(2, "0");

/**
 * Первый абзац описания — для карточек, где полный текст не помещается.
 * Абзацы разделены пустой строкой, как их набирают в форме контеста.
 */
export function firstParagraph(text: string): string {
  return text.trim().split(/\n\s*\n/)[0] ?? "";
}
