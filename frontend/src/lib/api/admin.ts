/** Изменения из админки — вызываются из браузера. */
"use client";

import { api } from "./client";
import type { AdminContest, AdminSubmission, PaymentSettings } from "./types";

export interface ContestInput {
  title: string;
  description: string;
  requirements: string[];
  prize_pool: string;
  deadline: string;
  status?: "draft" | "published" | "archived";
  is_featured?: boolean;
}

export async function createContest(input: ContestInput): Promise<AdminContest> {
  return api.post<AdminContest>("/api/admin/contests/", { ...input });
}

export async function updateContest(
  id: number,
  input: Partial<ContestInput>,
): Promise<AdminContest> {
  return api.patch<AdminContest>(`/api/admin/contests/${id}/`, { ...input });
}

export async function publishContest(id: number): Promise<AdminContest> {
  return api.post<AdminContest>(`/api/admin/contests/${id}/publish/`);
}

export interface ReviewInput {
  score: number | null;
  reviewer_notes: string;
  is_winner: boolean;
}

export async function saveReview(id: number, input: ReviewInput): Promise<AdminSubmission> {
  const data = await api.patch<{ submission: AdminSubmission }>(
    `/api/admin/submissions/${id}/`,
    { ...input },
  );
  return data.submission;
}

export async function savePaymentRequisites(requisites: string): Promise<PaymentSettings> {
  return api.put<PaymentSettings>("/api/admin/payments/requisites/", { requisites });
}

export async function deleteSubmission(id: number): Promise<void> {
  await api.delete<void>(`/api/admin/submissions/${id}/`);
}
