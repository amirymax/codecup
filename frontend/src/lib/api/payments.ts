/** Оплата участия — вызовы из браузера. */
"use client";

import { PUBLIC_API_URL } from "./config";
import { api } from "./client";
import { ApiRequestError } from "./errors";
import type { Participation } from "./types";

export async function getParticipation(slug: string): Promise<Participation> {
  return api.get<Participation>(`/api/contests/${slug}/participation/`);
}

/** Чек, загруженный на сайте. Идёт multipart, поэтому мимо api-обёртки. */
export async function uploadReceipt(slug: string, file: File): Promise<Participation> {
  const body = new FormData();
  body.append("receipt", file);

  const response = await fetch(`${PUBLIC_API_URL}/api/contests/${slug}/participation/receipt/`, {
    method: "POST",
    body,
    credentials: "include",
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiRequestError(response.status, payload, "Не удалось загрузить чек");
  }
  return payload as Participation;
}

export async function requestReceiptViaBot(
  slug: string,
): Promise<Participation & { bot_url: string }> {
  return api.post<Participation & { bot_url: string }>(
    `/api/contests/${slug}/participation/via-bot/`,
  );
}
