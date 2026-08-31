"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatMoney } from "@/lib/format";
import { contest as contestText, participation as t } from "@/messages/ru";
import type { Participation } from "@/lib/api/types";

import { ParticipateModal } from "./ParticipateModal";

/**
 * Кнопка в боковой панели контеста.
 *
 * Что на ней написано, зависит от того, платный ли контест и на каком этапе
 * оплата: пока взнос не принят, отправлять решение нельзя.
 */
export function ParticipationCta({
  slug,
  participation,
  isAuthenticated,
  hasSubmission,
}: {
  slug: string;
  participation: Participation;
  isAuthenticated: boolean;
  hasSubmission: boolean;
}) {
  const [modalOpen, setModalOpen] = useState(false);

  if (!isAuthenticated) {
    return (
      <Button className="w-full" asChild>
        <Link href={`/login?next=/contests/${slug}`}>
          {participation.is_paid ? t.loginToParticipate : contestText.loginToSubmit}
        </Link>
      </Button>
    );
  }

  if (participation.can_submit) {
    return (
      <Button className="w-full" variant={hasSubmission ? "outline" : "primary"} asChild>
        <Link href={`/contests/${slug}/submit`}>
          {hasSubmission ? contestText.editCta : contestText.submitCta}
        </Link>
      </Button>
    );
  }

  const status = participation.payment?.status;
  const label =
    status === "pending"
      ? t.statusPending
      : status === "awaiting_receipt" && participation.payment?.expects_receipt_in_bot
        ? t.waitingInBot
        : t.participateCta;

  return (
    <>
      <Button className="w-full" onClick={() => setModalOpen(true)}>
        {label}
      </Button>

      {modalOpen && (
        <ParticipateModal
          slug={slug}
          participation={participation}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}

/** Строка «Взнос за участие» в боковой панели. */
export function EntryFeeRow({ participation }: { participation: Participation }) {
  if (!participation.is_paid) return null;

  return (
    <div className="flex justify-between border-t border-line pt-4 text-[13.5px] text-muted">
      <span>{t.entryFee}</span>
      <span className="font-mono font-semibold text-text">
        {formatMoney(participation.entry_fee, participation.currency)}
      </span>
    </div>
  );
}
