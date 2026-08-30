/**
 * Обёртка над fetch для обоих окружений.
 *
 * Сессия живёт в httpOnly-куке, выставленной backend. В браузере она уходит
 * сама (`credentials: "include"`), а при рендеринге на сервере куки нужно
 * перекладывать вручную из входящего запроса — иначе серверный рендер
 * увидит гостя там, где пользователь уже вошёл.
 */

import { PUBLIC_API_URL, SERVER_API_URL } from "./config";
import { ApiRequestError } from "./errors";

type Json = Record<string, unknown> | unknown[];

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: Json;
  /** Заголовок Cookie для серверных запросов. */
  cookie?: string;
  /** Настройки кеша Next.js; по умолчанию данные всегда свежие. */
  cache?: RequestCache;
  revalidate?: number;
  signal?: AbortSignal;
}

const isServer = typeof window === "undefined";

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const base = isServer ? SERVER_API_URL : PUBLIC_API_URL;
  const headers: Record<string, string> = { Accept: "application/json" };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.cookie) {
    headers.Cookie = options.cookie;
  }

  const response = await fetch(`${base}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    // В браузере кука уходит только с credentials: include, потому что
    // фронтенд и API стоят на разных портах (и разных поддоменах в проде).
    credentials: isServer ? "omit" : "include",
    cache: options.cache ?? "no-store",
    next: options.revalidate === undefined ? undefined : { revalidate: options.revalidate },
    signal: options.signal,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await parseBody(response);

  if (!response.ok) {
    throw new ApiRequestError(
      response.status,
      payload as never,
      `Запрос завершился ошибкой ${response.status}`,
    );
  }

  return payload as T;
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options }),
  post: <T>(path: string, body?: Json, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: Json, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  patch: <T>(path: string, body?: Json, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

export { ApiRequestError };
