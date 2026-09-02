"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { track } from "@/lib/analytics";
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
      <Button
        className="w-full"
        onClick={() => {
          track("participate_click");
          setModalOpen(true);
        }}
      >
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

/**
 * Полоска состояния взноса на странице контеста.
 *
 * Решение админа должно быть видно сразу при заходе, а не только внутри
 * окна оплаты: иначе участник не понимает, почему нельзя отправить решение.
 */
type Tone = "green" | "blue" | "red";

export function PaymentStatusBanner({ participation }: { participation: Participation }) {
  const payment = participation.payment;
  if (!participation.is_paid || !payment) return null;

  const banners: Record<string, { tone: Tone; title: string; hint: string } | null> = {
    accepted: { tone: "green", title: t.bannerAccepted, hint: t.bannerAcceptedHint },
    pending: { tone: "blue", title: t.bannerPending, hint: t.bannerPendingHint },
    rejected: {
      tone: "red",
      title: t.bannerRejected,
      hint: payment.rejection_reason || t.bannerRejectedHint,
    },
    awaiting_receipt: payment.expects_receipt_in_bot
      ? { tone: "blue", title: t.bannerWaiting, hint: t.bannerWaitingHint }
      : null,
  };

  const banner = banners[payment.status];
  if (!banner) return null;

  const tones: Record<Tone, string> = {
    green: "border-green/25 bg-green/8 text-green-light",
    blue: "border-blue/20 bg-blue/8 text-blue-pale",
    red: "border-red/25 bg-red/8 text-red",
  };

  return (
    <div className={`rounded-[9px] border px-3.5 py-3 ${tones[banner.tone]}`}>
      <div className="text-[13.5px] font-semibold">{banner.title}</div>
      <p className="mt-0.5 text-[12.5px] opacity-80">{banner.hint}</p>
    </div>
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
