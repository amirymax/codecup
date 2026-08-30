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
  ContestDetail,
  FeaturedContest,
  MySubmission,
  Paginated,
  ProfileSubmission,
  PublicProfile,
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
