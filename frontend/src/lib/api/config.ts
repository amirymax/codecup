/**
 * Адреса backend.
 *
 * Браузер и сервер Next.js ходят в API по-разному, поэтому адресов два:
 * публичный — для браузера, внутренний — для рендеринга на сервере
 * (в Docker это может быть имя контейнера, а не localhost).
 */

export const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const SERVER_API_URL =
  process.env.INTERNAL_API_URL ?? PUBLIC_API_URL;
