/**
 * Удобные псевдонимы поверх сгенерированной схемы.
 *
 * Файл schema.ts генерируется командой `make schema` и правится только ею.
 * Здесь — только имена, которыми пользуется остальной фронтенд.
 */
import type { components } from "./schema";

type Schemas = components["schemas"];

// --- пользователи ---
export type User = Schemas["User"];
export type AuthStartResponse = Schemas["AuthStartResponse"];
export type AuthStatus = Schemas["AuthStatusResponse"]["status"];

// --- контесты ---
export type Contest = Schemas["ContestList"];
export type ContestDetail = Schemas["ContestDetail"];
export type ContestState = ContestDetail["state"];
export type FeaturedContest = Schemas["FeaturedContest"];

// --- заявки ---
export type MySubmission = Schemas["MySubmission"];
export type ProfileSubmission = Schemas["ProfileSubmission"];
export type SubmissionBadge = ProfileSubmission["display_status"];
export type PublicProfile = Schemas["PublicProfile"];

// --- оплата участия ---
export type Participation = Schemas["Participation"];
export type MyPayment = Schemas["MyPayment"];
export type PaymentStatus = MyPayment["status"];
export type Currency = ContestDetail["currency"];

// --- админка ---
export type AdminContest = Schemas["AdminContest"];
export type AdminSubmissionRow = Schemas["AdminSubmissionList"];
export type AdminSubmission = Schemas["AdminSubmissionDetail"];
export type ReviewNavigation = Schemas["Navigation"];
export type AdminStats = Schemas["AdminStats"];
export type AdminUser = Schemas["AdminUser"];
export type AdminPayment = Schemas["AdminPayment"];
export type Screening = Schemas["Screening"];

/** Формат ошибки, единый для всего API. */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/** Ответ DRF с постраничной разбивкой. */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
