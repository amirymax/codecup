/** Вызовы авторизации из браузера. */
"use client";

import { api } from "./client";
import type { AuthStartResponse, AuthStatus, User } from "./types";

export interface StartedLogin {
  nonce: string;
  clientSecret: string;
  deepLink: string;
  expiresIn: number;
}

export async function startTelegramLogin(): Promise<StartedLogin> {
  const data = await api.post<AuthStartResponse>("/api/auth/telegram/start/");
  return {
    nonce: data.nonce,
    clientSecret: data.client_secret,
    deepLink: data.deep_link,
    expiresIn: data.expires_in,
  };
}

export async function pollLoginStatus(nonce: string, signal?: AbortSignal): Promise<AuthStatus> {
  const data = await api.get<{ status: AuthStatus }>(
    `/api/auth/telegram/status/?nonce=${encodeURIComponent(nonce)}`,
    { signal },
  );
  return data.status;
}

/** Обмен подтверждённого кода на сессию: backend ставит httpOnly-куки. */
export async function exchangeLogin(nonce: string, clientSecret: string): Promise<User> {
  return api.post<User>("/api/auth/telegram/exchange/", {
    nonce,
    client_secret: clientSecret,
  });
}

export async function logout(): Promise<void> {
  await api.post<void>("/api/auth/logout/");
}
