/**
 * Функции для серверных компонентов.
 *
 * Каждая перекладывает куки входящего запроса в запрос к backend, поэтому
 * серверный рендер видит того же пользователя, что и браузер.
 */
import "server-only";

import { cookies } from "next/headers";

import { api } from "./client";
import { ApiRequestError } from "./errors";
import type {
  AdminContest,
  AdminPayment,
  AdminStats,
  AdminSubmission,
  AdminSubmissionRow,
  ContestDetail,
  FeaturedContest,
  MySubmission,
  Paginated,
  Participation,
  ProfileSubmission,
  PublicProfile,
  ReviewNavigation,
  Screening,
  User,
} from "./types";

async function cookieHeader(): Promise<string> {
  const store = await cookies();
  return store
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");
}

/** Текущий пользователь или null, если гость. Никогда не бросает 401. */
export async function getCurrentUser(): Promise<User | null> {
  try {
    return await api.get<User>("/api/auth/me/", { cookie: await cookieHeader() });
  } catch (error) {
    if (error instanceof ApiRequestError && error.isUnauthorized) {
      return null;
    }
    throw error;
  }
}

export async function getFeaturedContest(): Promise<FeaturedContest> {
  return api.get<FeaturedContest>("/api/contests/featured/", { cookie: await cookieHeader() });
}

export async function getContest(slug: string): Promise<ContestDetail> {
  return api.get<ContestDetail>(`/api/contests/${slug}/`, { cookie: await cookieHeader() });
}

export async function getParticipation(slug: string): Promise<Participation> {
  return api.get<Participation>(`/api/contests/${slug}/participation/`, {
    cookie: await cookieHeader(),
  });
}

export async function getMySubmissions(): Promise<Paginated<ProfileSubmission>> {
  return api.get<Paginated<ProfileSubmission>>("/api/me/submissions/", {
    cookie: await cookieHeader(),
  });
}

/** Своя заявка на контест; submission равен null, если её ещё нет. */
export async function getMySubmission(slug: string): Promise<MySubmission | null> {
  try {
    const data = await api.get<{ submission: MySubmission | null }>(
      `/api/contests/${slug}/submission/`,
      { cookie: await cookieHeader() },
    );
    return data.submission;
  } catch (error) {
    if (error instanceof ApiRequestError && error.isUnauthorized) {
      return null;
    }
    throw error;
  }
}

export async function getPublicProfile(username: string): Promise<PublicProfile> {
  return api.get<PublicProfile>(`/api/users/${username}/`, { cookie: await cookieHeader() });
}

// --- админка ---------------------------------------------------------------

export async function getAdminStats(): Promise<AdminStats> {
  return api.get<AdminStats>("/api/admin/stats/", { cookie: await cookieHeader() });
}

export async function getAdminContests(): Promise<Paginated<AdminContest>> {
  return api.get<Paginated<AdminContest>>("/api/admin/contests/", {
    cookie: await cookieHeader(),
  });
}

export async function getAdminContest(id: string): Promise<AdminContest> {
  return api.get<AdminContest>(`/api/admin/contests/${id}/`, { cookie: await cookieHeader() });
}

export async function getAdminPayments(
  query: Record<string, string> = {},
): Promise<Paginated<AdminPayment>> {
  const search = new URLSearchParams(query).toString();
  return api.get<Paginated<AdminPayment>>(`/api/admin/payments/${search ? `?${search}` : ""}`, {
    cookie: await cookieHeader(),
  });
}

export async function getAdminSubmissions(
  query: Record<string, string> = {},
): Promise<Paginated<AdminSubmissionRow>> {
  const search = new URLSearchParams(query).toString();
  return api.get<Paginated<AdminSubmissionRow>>(
    `/api/admin/submissions/${search ? `?${search}` : ""}`,
    { cookie: await cookieHeader() },
  );
}

export async function getAdminSubmission(id: string): Promise<{
  submission: AdminSubmission;
  navigation: ReviewNavigation;
  screening: Screening | null;
}> {
  return api.get(`/api/admin/submissions/${id}/`, { cookie: await cookieHeader() });
}
