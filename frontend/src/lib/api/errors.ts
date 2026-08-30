import type { ApiError } from "./types";

/** Ошибка API с машинным кодом из общего формата backend. */
export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: Partial<ApiError> | null, fallback: string) {
    const error = body?.error;
    super(error?.message ?? fallback);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = error?.code ?? "unknown_error";
    this.details = error?.details ?? {};
  }

  /** Ошибки конкретных полей формы: { github_url: "Ссылка обязательна." } */
  get fieldErrors(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const [field, value] of Object.entries(this.details)) {
      result[field] = Array.isArray(value) ? String(value[0]) : String(value);
    }
    return result;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}
