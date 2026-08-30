/** Работа с заявками из браузера. */
"use client";

import { api } from "./client";
import type { MySubmission } from "./types";

export interface SubmissionDraft {
  github_url: string;
  live_url: string;
  video_url: string;
  description: string;
}

interface Envelope {
  submission: MySubmission;
}

/** Сохранить черновик: незаполненные поля допустимы. */
export async function saveDraft(slug: string, draft: SubmissionDraft): Promise<MySubmission> {
  const data = await api.put<Envelope>(`/api/contests/${slug}/submission/`, { ...draft });
  return data.submission;
}

/** Отправить решение: backend проверит обязательные поля. */
export async function submitSolution(
  slug: string,
  draft: SubmissionDraft,
): Promise<MySubmission> {
  const data = await api.post<Envelope>(`/api/contests/${slug}/submission/submit/`, { ...draft });
  return data.submission;
}
