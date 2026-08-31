"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Avatar } from "@/components/Avatar";
import { ExternalIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import { ApiRequestError } from "@/lib/api/errors";
import { formatMoney, formatRelative } from "@/lib/format";
import { payments as t } from "@/messages/ru";
import type { AdminPayment } from "@/lib/api/types";

const STATUS_TONE: Record<string, string> = {
  pending: "bg-blue/10 border-blue/30 text-blue-light",
  accepted: "bg-green/10 border-green/30 text-green-light",
  rejected: "bg-red/10 border-red/25 text-red",
  awaiting_receipt: "bg-surface-3 border-line-2 text-muted",
};

const STATUS_LABEL: Record<string, string> = {
  pending: t.pending,
  accepted: t.accepted,
  rejected: t.rejected,
  awaiting_receipt: t.awaiting,
};

export function PaymentRow({ payment }: { payment: AdminPayment }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/admin/payments/${payment.id}/decision/`, { decision, reason });
      setRejecting(false);
      setReason("");
      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? (caught.fieldErrors.reason ?? caught.message)
          : t.saving,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="border-b border-[#1a1a1d] px-5 py-4 last:border-b-0">
      <div className="flex flex-wrap items-center gap-4">
        <Avatar name={payment.telegram_username || payment.username} size={30} />

        <div className="min-w-[180px] flex-1">
          <div className="text-sm font-semibold text-text">{payment.username}</div>
          <div className="text-[12.5px] text-muted-2">
            {payment.contest_title} · {formatRelative(payment.submitted_at ?? payment.created_at)}
          </div>
        </div>

        <div className="font-mono text-sm font-semibold text-text">
          {formatMoney(payment.amount, payment.currency)}
        </div>

        <span
          className={`shrink-0 rounded-full border px-3 py-[5px] text-xs font-semibold ${
            STATUS_TONE[payment.status] ?? STATUS_TONE.awaiting_receipt
          }`}
        >
          {STATUS_LABEL[payment.status] ?? payment.status}
        </span>

        {payment.receipt_url ? (
          <a
            href={payment.receipt_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-[7px] border border-line-2 px-3 py-1.5
                       text-[12.5px] font-semibold text-text-2 no-underline hover:border-line-3"
          >
            {t.openReceipt}
            <ExternalIcon size={13} />
          </a>
        ) : (
          <span className="text-[12.5px] text-muted-3">
            {payment.receipt_source === "telegram" ? t.receiptInTelegram : t.noReceipt}
          </span>
        )}

        {payment.status === "pending" && (
          <div className="flex gap-2">
            <Button size="sm" onClick={() => decide("accept")} disabled={busy}>
              {t.accept}
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={() => setRejecting((open) => !open)}
              disabled={busy}
            >
              {t.reject}
            </Button>
          </div>
        )}
      </div>

      {payment.rejection_reason && !rejecting && (
        <p className="mt-2 ml-11 text-[12.5px] text-red">{payment.rejection_reason}</p>
      )}

      {/* Причина обязательна: участник должен понимать, что исправить. */}
      {rejecting && (
        <div className="mt-3 ml-11 max-w-[520px]">
          <Textarea
            rows={2}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder={t.reasonPlaceholder}
            className="text-[13px]"
          />
          <div className="mt-2 flex gap-2">
            <Button size="sm" variant="danger" onClick={() => decide("reject")} disabled={busy}>
              {t.reject}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setRejecting(false)} disabled={busy}>
              {t.close}
            </Button>
          </div>
        </div>
      )}

      {error && <p className="mt-2 ml-11 text-[12.5px] text-red">{error}</p>}
    </div>
  );
}
