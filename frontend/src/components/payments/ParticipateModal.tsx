"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CheckIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { ApiRequestError } from "@/lib/api/errors";
import { requestReceiptViaBot, uploadReceipt } from "@/lib/api/payments";
import { formatMoney } from "@/lib/format";
import { participation as t } from "@/messages/ru";
import type { Participation } from "@/lib/api/types";

type View = "form" | "waiting_bot";

/**
 * Окно оплаты участия.
 *
 * Два пути прислать чек: файлом прямо здесь или сообщением в бот. Второй
 * нужен потому, что чек чаще всего лежит в телефоне, где уже открыт Telegram.
 */
export function ParticipateModal({
  slug,
  participation,
  onClose,
}: {
  slug: string;
  participation: Participation;
  onClose: () => void;
}) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const [view, setView] = useState<View>(
    participation.payment?.expects_receipt_in_bot ? "waiting_bot" : "form",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [botUrl, setBotUrl] = useState<string | null>(null);

  // Esc закрывает окно — привычное поведение для модальных окон.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const payment = participation.payment;
  const status = payment?.status;

  async function onFileChosen(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setBusy(true);
    setError(null);
    try {
      await uploadReceipt(slug, file);
      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? (caught.fieldErrors.receipt ?? caught.message)
          : t.uploading,
      );
    } finally {
      setBusy(false);
    }
  }

  async function onSendViaBot() {
    setBusy(true);
    setError(null);
    try {
      const result = await requestReceiptViaBot(slug);
      setBotUrl(result.bot_url);
      setView("waiting_bot");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof ApiRequestError ? caught.message : t.uploading);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-100 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={t.modalTitle}
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        className="cc-enter max-h-[90vh] w-full max-w-[460px] overflow-y-auto rounded-2xl
                   border border-line-2 bg-surface p-6 outline-none sm:p-7"
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <h2 className="text-lg font-extrabold">{t.modalTitle}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t.close}
            className="cursor-pointer border-none bg-transparent text-xl text-muted-2 hover:text-text"
          >
            ✕
          </button>
        </div>

        {status === "accepted" ? (
          <Result tone="green" title={t.statusAccepted} hint={t.statusAcceptedHint} />
        ) : status === "pending" ? (
          <Result tone="blue" title={t.statusPending} hint={t.statusPendingHint} />
        ) : (
          <>
            {status === "rejected" && (
              <div className="mb-5 rounded-lg border border-red/25 bg-red/8 px-3.5 py-3 text-[13.5px] text-red">
                <strong>{t.statusRejected}.</strong>{" "}
                {payment?.rejection_reason || t.sendAnother}
              </div>
            )}

            <div className="mb-5 rounded-xl border border-line bg-surface-2 p-4">
              <div className="mb-1 text-[11.5px] font-semibold tracking-wide text-muted-2 uppercase">
                {t.entryFee}
              </div>
              <div className="font-mono text-2xl font-bold text-green-light">
                {formatMoney(participation.entry_fee, participation.currency)}
              </div>
            </div>

            {view === "waiting_bot" ? (
              <BotWaiting botUrl={botUrl} onBack={() => setView("form")} />
            ) : (
              <>
                <p className="mb-4 text-[13.5px] leading-relaxed text-muted">{t.modalIntro}</p>

                <div className="mb-5">
                  <div className="mb-1.5 text-[11.5px] font-semibold tracking-wide text-muted-2 uppercase">
                    {t.requisitesLabel}
                  </div>
                  <pre
                    className="rounded-lg border border-line bg-surface-2 p-3.5 font-mono
                               text-[13px] leading-relaxed whitespace-pre-wrap text-text-2"
                  >
                    {participation.requisites}
                  </pre>
                </div>

                <input
                  ref={fileInput}
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={onFileChosen}
                  className="hidden"
                />
                <Button
                  className="w-full"
                  onClick={() => fileInput.current?.click()}
                  disabled={busy}
                >
                  {busy ? t.uploading : t.uploadLabel}
                </Button>
                <p className="mt-1.5 text-center text-[11.5px] text-muted-3">{t.uploadHint}</p>

                <div className="my-4 text-center text-[12px] text-muted-3">{t.orSendViaBot}</div>

                <Button
                  variant="telegram"
                  className="w-full"
                  onClick={onSendViaBot}
                  disabled={busy}
                >
                  {t.sendViaBot}
                </Button>
              </>
            )}

            {error && (
              <p className="mt-4 rounded-lg border border-red/25 bg-red/8 px-3 py-2.5 text-[13px] text-red">
                {error}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function BotWaiting({ botUrl, onBack }: { botUrl: string | null; onBack: () => void }) {
  return (
    <div className="py-2 text-center">
      <div
        className="mx-auto mb-5 flex size-14 items-center justify-center rounded-full border
                   border-blue/25 bg-blue/10"
        style={{ animation: "cc-pulse 1.8s infinite" }}
      >
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M21.5 3.5L2.5 11l6 2.3m13-9.8l-4 17-6.7-5.2m10.7-11.8l-10.7 11.8m0 0L9.3 20"
            stroke="#60a5fa"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h3 className="mb-2 text-base font-bold">{t.waitingInBot}</h3>
      <p className="mb-6 text-[13.5px] leading-relaxed text-muted">{t.waitingInBotHint}</p>

      {botUrl && (
        <Button variant="telegram" className="mb-3 w-full" asChild>
          <a href={botUrl} target="_blank" rel="noopener noreferrer">
            {t.openBot}
          </a>
        </Button>
      )}
      <button
        type="button"
        onClick={onBack}
        className="cursor-pointer border-none bg-transparent text-[13px] text-muted-2 underline"
      >
        {t.uploadLabel}
      </button>
    </div>
  );
}

function Result({ tone, title, hint }: { tone: "green" | "blue"; title: string; hint: string }) {
  const tones = {
    green: "border-green/30 bg-green/10 text-green-light",
    blue: "border-blue/25 bg-blue/10 text-blue-light",
  } as const;

  return (
    <div className="py-4 text-center">
      <div
        className={`mx-auto mb-5 flex size-14 items-center justify-center rounded-full border ${tones[tone]}`}
      >
        <CheckIcon size={26} />
      </div>
      <h3 className="mb-2 text-base font-bold">{title}</h3>
      <p className="text-[13.5px] leading-relaxed text-muted">{hint}</p>
    </div>
  );
}
