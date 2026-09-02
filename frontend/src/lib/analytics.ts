"use client";

import { PUBLIC_API_URL } from "./api/config";

/**
 * Отправка события в статистику.
 *
 * Мимо обычного клиента API намеренно: ответ нам не нужен, а упавшая
 * статистика не должна ломать страницу. keepalive — чтобы запрос пережил
 * переход на другую страницу, иначе последний клик всегда терялся бы.
 */
export function track(name: string, path?: string): void {
  try {
    void fetch(`${PUBLIC_API_URL}/api/analytics/event/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, path: path ?? window.location.pathname }),
      credentials: "include",
      keepalive: true,
    }).catch(() => {});
  } catch {
    // Статистика — не повод показывать пользователю ошибку.
  }
}
